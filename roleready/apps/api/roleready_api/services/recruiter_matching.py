"""
Recruiter and Enterprise Matching Service
Handles job description analysis, candidate matching, and enterprise features
"""

from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime
import asyncio
from sentence_transformers import SentenceTransformer
from roleready_api.core.supabase import supabase_client
from .multilingual import multilingual_service

logger = logging.getLogger(__name__)

class RecruiterMatchingService:
    def __init__(self):
        self.embedding_model = multilingual_service.embedding_model

    async def create_job_description(
        self,
        team_id: str,
        title: str,
        description: str,
        requirements: List[str] = None,
        skills: List[str] = None,
        location: str = None,
        salary_range: Dict = None,
        experience_level: str = None,
        job_type: str = "full-time",
        remote_friendly: bool = False,
        created_by: str = None
    ) -> Dict:
        """
        Create a new job description and generate embeddings
        """
        try:
            # Detect language
            language = multilingual_service.detect_language(description)
            
            # Generate embeddings for the job description
            full_text = f"{title} {description} {' '.join(requirements or [])} {' '.join(skills or [])}"
            
            # Translate to English for embedding if needed
            if language != 'en':
                full_text = multilingual_service.translate_text(full_text, 'en', language)
            
            embeddings = multilingual_service.get_multilingual_embeddings([full_text])
            
            job_data = {
                "team_id": team_id,
                "title": title,
                "company": None,  # Could be extracted or added separately
                "description": description,
                "requirements": requirements or [],
                "skills": skills or [],
                "location": location,
                "salary_range": salary_range,
                "experience_level": experience_level,
                "job_type": job_type,
                "remote_friendly": remote_friendly,
                "embeddings": embeddings[0] if embeddings else [],
                "language": language,
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = supabase_client.table("job_descriptions").insert(job_data).execute()
            
            if result.data:
                job_id = result.data[0]["id"]
                logger.info(f"Job description created: {job_id} for team {team_id}")
                return {"success": True, "job_id": job_id, "job": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create job description"}
                
        except Exception as e:
            logger.error(f"Error creating job description: {e}")
            return {"success": False, "error": str(e)}

    async def find_candidates(
        self,
        job_description_id: int,
        limit: int = 50,
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Find matching candidates for a job description
        """
        try:
            # Get job description
            job_result = supabase_client.table("job_descriptions").select("*").eq("id", job_description_id).execute()
            
            if not job_result.data:
                return []
            
            job = job_result.data[0]
            job_embeddings = job.get("embeddings", [])
            
            if not job_embeddings:
                logger.warning(f"No embeddings found for job {job_description_id}")
                return []
            
            # Get all resumes with embeddings
            resumes_result = supabase_client.table("resumes").select(
                "id, user_id, summary, skills, experience, embeddings, language, created_at"
            ).not_.is_("embeddings", "null").execute()
            
            if not resumes_result.data:
                return []
            
            candidates = []
            
            for resume in resumes_result.data:
                resume_embeddings = resume.get("embeddings", [])
                
                if not resume_embeddings:
                    continue
                
                # Calculate similarity score
                similarity_score = self._calculate_similarity(job_embeddings, resume_embeddings)
                
                if similarity_score >= min_score:
                    # Calculate skill alignment
                    skill_alignment = self._calculate_skill_alignment(
                        job.get("skills", []), 
                        resume.get("skills", [])
                    )
                    
                    # Calculate experience alignment
                    experience_alignment = self._calculate_experience_alignment(
                        job.get("requirements", []), 
                        resume.get("experience", [])
                    )
                    
                    # Overall fit score (weighted combination)
                    overall_fit = (
                        similarity_score * 0.4 +
                        skill_alignment * 0.4 +
                        experience_alignment * 0.2
                    )
                    
                    # Find matched and missing skills
                    matched_skills, missing_skills = self._analyze_skills(
                        job.get("skills", []), 
                        resume.get("skills", [])
                    )
                    
                    candidate = {
                        "resume_id": resume["id"],
                        "user_id": resume["user_id"],
                        "match_score": round(similarity_score, 3),
                        "skill_alignment": round(skill_alignment, 3),
                        "experience_alignment": round(experience_alignment, 3),
                        "overall_fit": round(overall_fit, 3),
                        "matched_skills": matched_skills,
                        "missing_skills": missing_skills,
                        "language": resume.get("language", "en"),
                        "created_at": resume.get("created_at")
                    }
                    
                    candidates.append(candidate)
            
            # Sort by overall fit score
            candidates.sort(key=lambda x: x["overall_fit"], reverse=True)
            
            # Store matches in database
            await self._store_candidate_matches(job_description_id, candidates[:limit])
            
            return candidates[:limit]
            
        except Exception as e:
            logger.error(f"Error finding candidates: {e}")
            return []

    def _calculate_similarity(self, embeddings1: List[float], embeddings2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors
        """
        try:
            import numpy as np
            
            vec1 = np.array(embeddings1)
            vec2 = np.array(embeddings2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def _calculate_skill_alignment(self, job_skills: List[str], resume_skills: List[str]) -> float:
        """
        Calculate skill alignment score
        """
        if not job_skills:
            return 0.0
        
        job_skills_lower = [skill.lower() for skill in job_skills]
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        
        matched_skills = 0
        for job_skill in job_skills_lower:
            # Check for exact or partial matches
            if any(job_skill in resume_skill or resume_skill in job_skill 
                   for resume_skill in resume_skills_lower):
                matched_skills += 1
        
        return matched_skills / len(job_skills)

    def _calculate_experience_alignment(self, job_requirements: List[str], resume_experience: List[str]) -> float:
        """
        Calculate experience alignment score
        """
        if not job_requirements or not resume_experience:
            return 0.0
        
        job_text = " ".join(job_requirements).lower()
        experience_text = " ".join(resume_experience).lower()
        
        # Simple keyword matching for now
        # In production, you'd want more sophisticated NLP
        matched_keywords = 0
        total_keywords = len(job_requirements)
        
        for requirement in job_requirements:
            requirement_lower = requirement.lower()
            if any(requirement_lower in exp or exp in requirement_lower for exp in resume_experience):
                matched_keywords += 1
        
        return matched_keywords / total_keywords if total_keywords > 0 else 0.0

    def _analyze_skills(self, job_skills: List[str], resume_skills: List[str]) -> Tuple[List[str], List[str]]:
        """
        Analyze matched and missing skills
        """
        job_skills_lower = [skill.lower() for skill in job_skills]
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills:
            job_skill_lower = job_skill.lower()
            
            # Check for matches
            matched = False
            for resume_skill in resume_skills:
                resume_skill_lower = resume_skill.lower()
                if (job_skill_lower in resume_skill_lower or 
                    resume_skill_lower in job_skill_lower or
                    job_skill_lower == resume_skill_lower):
                    matched_skills.append(resume_skill)
                    matched = True
                    break
            
            if not matched:
                missing_skills.append(job_skill)
        
        return matched_skills, missing_skills
    
    async def _store_candidate_matches(self, job_description_id: int, candidates: List[Dict]) -> None:
        """
        Store candidate matches in the database
        """
        try:
            match_records = []
            for candidate in candidates:
                match_record = {
                    "job_description_id": job_description_id,
                    "resume_id": candidate["resume_id"],
                    "match_score": candidate["match_score"],
                    "skill_alignment": candidate["skill_alignment"],
                    "experience_alignment": candidate["experience_alignment"],
                    "overall_fit": candidate["overall_fit"],
                    "matched_skills": candidate["matched_skills"],
                    "missing_skills": candidate["missing_skills"],
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat()
                }
                match_records.append(match_record)
            
            if match_records:
                supabase_client.table("candidate_matches").insert(match_records).execute()
                logger.info(f"Stored {len(match_records)} candidate matches for job {job_description_id}")
                
        except Exception as e:
            logger.error(f"Error storing candidate matches: {e}")

    async def update_match_status(
        self,
        match_id: int,
        status: str,
        reviewed_by: str = None,
        notes: str = None
    ) -> Dict:
        """
        Update the status of a candidate match
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if reviewed_by:
                update_data["reviewed_by"] = reviewed_by
                update_data["reviewed_at"] = datetime.utcnow().isoformat()
            
            if notes:
                update_data["notes"] = notes
            
            result = supabase_client.table("candidate_matches").update(update_data).eq("id", match_id).execute()
            
            if result.data:
                return {"success": True, "match": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update match status"}
                
        except Exception as e:
            logger.error(f"Error updating match status: {e}")
            return {"success": False, "error": str(e)}

    async def get_team_analytics(self, team_id: str, days_back: int = 30) -> Dict:
        """
        Get analytics for a team's recruiting activities
        """
        try:
            cutoff_date = datetime.utcnow().replace(day=datetime.utcnow().day - days_back)
            
            # Get job descriptions
            jobs_result = supabase_client.table("job_descriptions").select("*").eq("team_id", team_id).gte(
                "created_at", cutoff_date.isoformat()
            ).execute()
            
            jobs = jobs_result.data or []
            
            # Get candidate matches
            job_ids = [job["id"] for job in jobs]
            matches = []
            if job_ids:
                matches_result = supabase_client.table("candidate_matches").select("*").in_(
                    "job_description_id", job_ids
                ).execute()
                matches = matches_result.data or []
            
            # Calculate metrics
            total_jobs = len(jobs)
            total_matches = len(matches)
            avg_matches_per_job = total_matches / total_jobs if total_jobs > 0 else 0
            
            # Status breakdown
            status_counts = {}
            for match in matches:
                status = match.get("status", "pending")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Score distribution
            scores = [match["overall_fit"] for match in matches if match.get("overall_fit")]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Most common missing skills
            missing_skills = []
            for match in matches:
                missing_skills.extend(match.get("missing_skills", []))
            
            skill_counts = {}
            for skill in missing_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            top_missing_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            analytics = {
                "period_days": days_back,
                "total_jobs": total_jobs,
                "total_matches": total_matches,
                "avg_matches_per_job": round(avg_matches_per_job, 2),
                "status_breakdown": status_counts,
                "avg_match_score": round(avg_score, 3),
                "top_missing_skills": top_missing_skills,
                "jobs": jobs,
                "matches": matches
            }
            
            # Store analytics
            analytics_record = {
                "team_id": team_id,
                "metric_name": "recruiting_analytics",
                "metric_value": analytics,
                "period_start": cutoff_date.isoformat(),
                "period_end": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase_client.table("enterprise_analytics").insert(analytics_record).execute()
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting team analytics: {e}")
            return {"error": str(e)}

    async def batch_upload_jobs(self, team_id: str, jobs_data: List[Dict], created_by: str = None) -> Dict:
        """
        Batch upload multiple job descriptions
        """
        try:
            created_jobs = []
            failed_jobs = []
            
            for job_data in jobs_data:
                result = await self.create_job_description(
                    team_id=team_id,
                    title=job_data.get("title", ""),
                    description=job_data.get("description", ""),
                    requirements=job_data.get("requirements", []),
                    skills=job_data.get("skills", []),
                    location=job_data.get("location"),
                    salary_range=job_data.get("salary_range"),
                    experience_level=job_data.get("experience_level"),
                    job_type=job_data.get("job_type", "full-time"),
                    remote_friendly=job_data.get("remote_friendly", False),
                    created_by=created_by
                )
                
                if result["success"]:
                    created_jobs.append(result["job"])
                else:
                    failed_jobs.append({"job_data": job_data, "error": result["error"]})
            
            return {
                "success": True,
                "created_count": len(created_jobs),
                "failed_count": len(failed_jobs),
                "created_jobs": created_jobs,
                "failed_jobs": failed_jobs
            }
            
        except Exception as e:
            logger.error(f"Error in batch upload: {e}")
            return {"success": False, "error": str(e)}

# Global instance
recruiter_matching_service = RecruiterMatchingService()