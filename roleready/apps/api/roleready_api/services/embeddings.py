"""
Enhanced Embeddings Service with Multilingual Support
Handles embedding generation using multilingual SentenceTransformer model
"""

from typing import Dict, List, Optional, Tuple
import logging
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from roleready_api.core.supabase import supabase_client
from .multilingual import multilingual_service

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        # Use multilingual model for cross-language semantic search
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        
        # Cache for embeddings to avoid recomputation
        self.embedding_cache = {}

    async def generate_resume_embeddings(self, resume_data: Dict) -> List[float]:
        """
        Generate embeddings for resume content using multilingual model
        """
        try:
            # Combine resume content for embedding
            summary = resume_data.get("summary", "")
            skills = resume_data.get("skills", [])
            experience = resume_data.get("experience", [])
            
            # Create text for embedding
            combined_text = summary
            
            # Add skills
            if skills:
                combined_text += " " + " ".join(skills[:20])  # Limit to top 20 skills
            
            # Add experience (limit to avoid too long text)
            if experience:
                combined_text += " " + " ".join(experience[:10])
            
            # Clean and truncate text
            combined_text = combined_text.strip()[:4000]  # Limit to 4000 chars
            
            if not combined_text:
                logger.warning("No text content found for embedding generation")
                return []
            
            # Generate embeddings
            embeddings = self.model.encode([combined_text], convert_to_tensor=False)
            
            if len(embeddings) > 0:
                return embeddings[0].tolist()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating resume embeddings: {e}")
            return []

    async def generate_job_description_embeddings(self, job_data: Dict) -> List[float]:
        """
        Generate embeddings for job description content
        """
        try:
            title = job_data.get("title", "")
            description = job_data.get("description", "")
            requirements = job_data.get("requirements", [])
            skills = job_data.get("skills", [])
            
            # Combine job content
            combined_text = f"{title} {description}"
            
            if requirements:
                combined_text += " " + " ".join(requirements)
            
            if skills:
                combined_text += " " + " ".join(skills)
            
            # Clean and truncate
            combined_text = combined_text.strip()[:4000]
            
            if not combined_text:
                logger.warning("No text content found for job embedding generation")
                return []
            
            # Generate embeddings
            embeddings = self.model.encode([combined_text], convert_to_tensor=False)
            
            if len(embeddings) > 0:
                return embeddings[0].tolist()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating job description embeddings: {e}")
            return []

    async def calculate_similarity(self, embeddings1: List[float], embeddings2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors
        """
        try:
            if not embeddings1 or not embeddings2:
                return 0.0
            
            vec1 = np.array(embeddings1)
            vec2 = np.array(embeddings2)
            
            # Ensure vectors have the same dimension
            if len(vec1) != len(vec2):
                logger.warning(f"Embedding dimension mismatch: {len(vec1)} vs {len(vec2)}")
                return 0.0
            
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

    async def find_similar_resumes(
        self, 
        query_embeddings: List[float], 
        limit: int = 10,
        min_similarity: float = 0.3,
        exclude_resume_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find resumes similar to query embeddings
        """
        try:
            # Get all resumes with embeddings
            query = supabase_client.table("resumes").select(
                "id, user_id, summary, skills, experience, embeddings, language, created_at"
            ).not_.is_("embeddings", "null")
            
            if exclude_resume_id:
                query = query.neq("id", exclude_resume_id)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            similarities = []
            
            for resume in result.data:
                resume_embeddings = resume.get("embeddings", [])
                
                if not resume_embeddings:
                    continue
                
                similarity = await self.calculate_similarity(query_embeddings, resume_embeddings)
                
                if similarity >= min_similarity:
                    similarities.append({
                        "resume_id": resume["id"],
                        "user_id": resume["user_id"],
                        "similarity": similarity,
                        "language": resume.get("language", "en"),
                        "created_at": resume.get("created_at")
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar resumes: {e}")
            return []

    async def find_similar_job_descriptions(
        self,
        query_embeddings: List[float],
        limit: int = 10,
        min_similarity: float = 0.3,
        team_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find job descriptions similar to query embeddings
        """
        try:
            # Get job descriptions with embeddings
            query = supabase_client.table("job_descriptions").select(
                "id, team_id, title, description, requirements, skills, embeddings, language, created_at"
            ).not_.is_("embeddings", "null")
            
            if team_id:
                query = query.eq("team_id", team_id)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            similarities = []
            
            for job in result.data:
                job_embeddings = job.get("embeddings", [])
                
                if not job_embeddings:
                    continue
                
                similarity = await self.calculate_similarity(query_embeddings, job_embeddings)
                
                if similarity >= min_similarity:
                    similarities.append({
                        "job_id": job["id"],
                        "team_id": job["team_id"],
                        "title": job["title"],
                        "similarity": similarity,
                        "language": job.get("language", "en"),
                        "created_at": job.get("created_at")
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar job descriptions: {e}")
            return []

    async def update_resume_embeddings(self, resume_id: str, resume_data: Dict) -> bool:
        """
        Update embeddings for a resume and store in database
        """
        try:
            embeddings = await self.generate_resume_embeddings(resume_data)
            
            if embeddings:
                # Update database
                result = supabase_client.table("resumes").update({
                    "embeddings": embeddings,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", resume_id).execute()
                
                if result.data:
                    logger.info(f"Updated embeddings for resume {resume_id}")
                    return True
                else:
                    logger.error(f"Failed to update embeddings for resume {resume_id}")
                    return False
            else:
                logger.warning(f"No embeddings generated for resume {resume_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating resume embeddings: {e}")
            return False

    async def update_job_description_embeddings(self, job_id: int, job_data: Dict) -> bool:
        """
        Update embeddings for a job description and store in database
        """
        try:
            embeddings = await self.generate_job_description_embeddings(job_data)
            
            if embeddings:
                # Update database
                result = supabase_client.table("job_descriptions").update({
                    "embeddings": embeddings,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", job_id).execute()
                
                if result.data:
                    logger.info(f"Updated embeddings for job description {job_id}")
                    return True
                else:
                    logger.error(f"Failed to update embeddings for job description {job_id}")
                    return False
            else:
                logger.warning(f"No embeddings generated for job description {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating job description embeddings: {e}")
            return False

    async def batch_update_embeddings(self, resume_ids: List[str] = None, job_ids: List[int] = None) -> Dict:
        """
        Batch update embeddings for multiple resumes and/or job descriptions
        """
        try:
            results = {
                "resumes": {"processed": 0, "successful": 0, "failed": 0},
                "jobs": {"processed": 0, "successful": 0, "failed": 0}
            }
            
            # Update resume embeddings
            if resume_ids:
                for resume_id in resume_ids:
                    try:
                        # Get resume data
                        result = supabase_client.table("resumes").select("*").eq("id", resume_id).execute()
                        
                        if result.data:
                            resume_data = result.data[0]
                            success = await self.update_resume_embeddings(resume_id, resume_data)
                            
                            results["resumes"]["processed"] += 1
                            if success:
                                results["resumes"]["successful"] += 1
                            else:
                                results["resumes"]["failed"] += 1
                        else:
                            results["resumes"]["failed"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing resume {resume_id}: {e}")
                        results["resumes"]["failed"] += 1
            
            # Update job description embeddings
            if job_ids:
                for job_id in job_ids:
                    try:
                        # Get job data
                        result = supabase_client.table("job_descriptions").select("*").eq("id", job_id).execute()
                        
                        if result.data:
                            job_data = result.data[0]
                            success = await self.update_job_description_embeddings(job_id, job_data)
                            
                            results["jobs"]["processed"] += 1
                            if success:
                                results["jobs"]["successful"] += 1
                            else:
                                results["jobs"]["failed"] += 1
                        else:
                            results["jobs"]["failed"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing job {job_id}: {e}")
                        results["jobs"]["failed"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch update embeddings: {e}")
            return {"error": str(e)}

# Global instance
embeddings_service = EmbeddingsService()