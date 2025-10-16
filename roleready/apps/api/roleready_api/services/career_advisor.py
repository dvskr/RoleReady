"""
Career Path Advisor Service
Analyzes resume content and provides career guidance, skill gap analysis,
and learning path recommendations
"""

from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime
from collections import Counter
import re
from sentence_transformers import SentenceTransformer
from roleready_api.core.supabase import supabase_client
from .multilingual import multilingual_service

logger = logging.getLogger(__name__)

class CareerAdvisorService:
    def __init__(self):
        self.embedding_model = multilingual_service.embedding_model
        
        # Skill taxonomies for different domains
        self.skill_taxonomies = {
            "data_science": {
                "programming": ["python", "r", "sql", "scala", "julia"],
                "ml_frameworks": ["tensorflow", "pytorch", "scikit-learn", "keras", "spark"],
                "tools": ["jupyter", "pandas", "numpy", "matplotlib", "seaborn", "plotly"],
                "cloud": ["aws", "azure", "gcp", "databricks", "snowflake"],
                "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch"],
                "statistics": ["statistical modeling", "hypothesis testing", "a/b testing", "bayesian statistics"],
                "specializations": ["nlp", "computer vision", "deep learning", "time series", "recommendation systems"]
            },
            "software_engineering": {
                "languages": ["python", "java", "javascript", "typescript", "go", "rust", "c++", "c#"],
                "frameworks": ["react", "angular", "vue", "django", "flask", "spring", "express", "fastapi"],
                "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra"],
                "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
                "devops": ["ci/cd", "jenkins", "github actions", "gitlab", "ansible", "chef"],
                "testing": ["unit testing", "integration testing", "jest", "pytest", "selenium"],
                "architecture": ["microservices", "rest", "graphql", "event-driven", "domain-driven design"]
            },
            "product_management": {
                "methodologies": ["agile", "scrum", "kanban", "lean", "design thinking"],
                "tools": ["jira", "confluence", "figma", "sketch", "invision", "miro"],
                "analytics": ["google analytics", "mixpanel", "amplitude", "tableau", "power bi"],
                "research": ["user research", "market research", "competitive analysis", "personas"],
                "strategy": ["product strategy", "roadmapping", "feature prioritization", "go-to-market"],
                "communication": ["stakeholder management", "presentation skills", "technical writing"]
            },
            "marketing": {
                "digital": ["seo", "sem", "ppc", "social media marketing", "content marketing"],
                "tools": ["google ads", "facebook ads", "hubspot", "marketo", "salesforce"],
                "analytics": ["google analytics", "adobe analytics", "mixpanel", "amplitude"],
                "creative": ["photoshop", "illustrator", "canva", "video editing", "copywriting"],
                "strategy": ["brand strategy", "campaign planning", "market research", "customer segmentation"],
                "automation": ["email marketing", "marketing automation", "lead nurturing", "crm"]
            }
        }
        
        # Course recommendations from various platforms
        self.course_recommendations = {
            "data_science": {
                "python": [
                    {"title": "Python for Data Science", "platform": "Coursera", "url": "https://coursera.org/learn/python-for-data-science"},
                    {"title": "Data Science with Python", "platform": "edX", "url": "https://edx.org/course/data-science-with-python"}
                ],
                "machine_learning": [
                    {"title": "Machine Learning", "platform": "Coursera", "url": "https://coursera.org/learn/machine-learning"},
                    {"title": "Deep Learning Specialization", "platform": "Coursera", "url": "https://coursera.org/specializations/deep-learning"}
                ],
                "sql": [
                    {"title": "SQL for Data Science", "platform": "Coursera", "url": "https://coursera.org/learn/sql-for-data-science"},
                    {"title": "Advanced SQL", "platform": "Udemy", "url": "https://udemy.com/course/advanced-sql"}
                ]
            },
            "software_engineering": {
                "python": [
                    {"title": "Python Programming", "platform": "Coursera", "url": "https://coursera.org/learn/python-programming"},
                    {"title": "Complete Python Bootcamp", "platform": "Udemy", "url": "https://udemy.com/course/complete-python-bootcamp"}
                ],
                "javascript": [
                    {"title": "JavaScript Algorithms and Data Structures", "platform": "freeCodeCamp", "url": "https://freecodecamp.org/learn/javascript-algorithms-and-data-structures"},
                    {"title": "Modern JavaScript", "platform": "Udemy", "url": "https://udemy.com/course/modern-javascript"}
                ],
                "cloud": [
                    {"title": "AWS Fundamentals", "platform": "Coursera", "url": "https://coursera.org/learn/aws-fundamentals"},
                    {"title": "Docker and Kubernetes", "platform": "Udemy", "url": "https://udemy.com/course/docker-and-kubernetes"}
                ]
            }
        }

    async def analyze_career_path(
        self, 
        user_id: str, 
        resume_id: str, 
        resume_content: Dict,
        target_domain: Optional[str] = None
    ) -> Dict:
        """
        Analyze resume and provide career guidance
        """
        try:
            # Extract skills from resume
            skills = resume_content.get("skills", [])
            experience = resume_content.get("experience", [])
            summary = resume_content.get("summary", "")
            
            # Determine primary domain if not specified
            if not target_domain:
                target_domain = self._detect_primary_domain(skills, experience, summary)
            
            # Analyze skill gaps
            skill_gaps = self._analyze_skill_gaps(skills, target_domain)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(skill_gaps, target_domain)
            
            # Calculate alignment score
            alignment_score = self._calculate_alignment_score(skills, target_domain)
            
            # Store insights
            insight_data = {
                "user_id": user_id,
                "resume_id": resume_id,
                "domain": target_domain,
                "missing_skills": skill_gaps["missing"],
                "recommended_skills": recommendations["skills"],
                "skill_gaps": skill_gaps,
                "learning_paths": recommendations["courses"],
                "alignment_score": alignment_score,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save to database
            result = supabase_client.table("career_insights").insert(insight_data).execute()
            
            if result.data:
                insight_id = result.data[0]["id"]
                logger.info(f"Career insights saved for user {user_id}, domain: {target_domain}")
            else:
                insight_id = None
                logger.warning("Failed to save career insights to database")
            
            return {
                "domain": target_domain,
                "alignment_score": alignment_score,
                "missing_skills": skill_gaps["missing"],
                "recommended_skills": recommendations["skills"],
                "learning_paths": recommendations["courses"],
                "skill_gaps": skill_gaps,
                "insight_id": insight_id
            }
            
        except Exception as e:
            logger.error(f"Error analyzing career path: {e}")
            return {"error": str(e)}

    def _detect_primary_domain(self, skills: List[str], experience: List[str], summary: str) -> str:
        """
        Detect the primary career domain based on skills and experience
        """
        all_text = " ".join(skills + experience + [summary]).lower()
        
        domain_scores = {}
        for domain, taxonomy in self.skill_taxonomies.items():
            score = 0
            for category, domain_skills in taxonomy.items():
                for skill in domain_skills:
                    if skill.lower() in all_text:
                        score += 1
            
            # Weight recent skills more heavily
            for skill in skills[:10]:  # Top 10 skills
                for category, domain_skills in taxonomy.items():
                    if skill.lower() in [s.lower() for s in domain_skills]:
                        score += 2
            
            domain_scores[domain] = score
        
        # Return domain with highest score, default to software_engineering
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain if domain_scores[best_domain] > 0 else "software_engineering"

    def _analyze_skill_gaps(self, current_skills: List[str], domain: str) -> Dict:
        """
        Analyze gaps between current skills and domain requirements
        """
        if domain not in self.skill_taxonomies:
            return {"missing": [], "weak": [], "strong": []}
        
        current_skills_lower = [skill.lower() for skill in current_skills]
        domain_skills = self.skill_taxonomies[domain]
        
        missing_skills = []
        weak_skills = []
        strong_skills = []
        
        for category, required_skills in domain_skills.items():
            for skill in required_skills:
                # Check for exact matches
                if skill.lower() in current_skills_lower:
                    strong_skills.append(skill)
                else:
                    # Check for partial matches
                    partial_match = any(skill.lower() in current_skill or current_skill in skill.lower() 
                                     for current_skill in current_skills_lower)
                    if partial_match:
                        weak_skills.append(skill)
                    else:
                        missing_skills.append(skill)
        
        return {
            "missing": missing_skills[:10],  # Top 10 missing skills
            "weak": weak_skills[:5],
            "strong": strong_skills[:10]
        }

    def _generate_recommendations(self, skill_gaps: Dict, domain: str) -> Dict:
        """
        Generate learning recommendations based on skill gaps
        """
        recommended_skills = skill_gaps["missing"][:5]  # Top 5 missing skills
        courses = []
        
        if domain in self.course_recommendations:
            for skill in recommended_skills:
                skill_lower = skill.lower()
                
                # Find matching course category
                for category, course_list in self.course_recommendations[domain].items():
                    if skill_lower in category or any(skill_lower in course_skill.lower() for course_skill in [category]):
                        courses.extend(course_list[:2])  # Top 2 courses per skill
        
        # Remove duplicates
        seen_urls = set()
        unique_courses = []
        for course in courses:
            if course["url"] not in seen_urls:
                seen_urls.add(course["url"])
                unique_courses.append(course)
        
        return {
            "skills": recommended_skills,
            "courses": unique_courses[:10]  # Top 10 courses
        }

    def _calculate_alignment_score(self, skills: List[str], domain: str) -> float:
        """
        Calculate alignment score between current skills and domain requirements
        """
        if domain not in self.skill_taxonomies:
            return 0.0
        
        domain_skills = self.skill_taxonomies[domain]
        all_required_skills = []
        for category_skills in domain_skills.values():
            all_required_skills.extend(category_skills)
        
        current_skills_lower = [skill.lower() for skill in skills]
        matched_skills = 0
        
        for required_skill in all_required_skills:
            # Check for exact or partial matches
            if (required_skill.lower() in current_skills_lower or 
                any(required_skill.lower() in current_skill or current_skill in required_skill.lower() 
                    for current_skill in current_skills_lower)):
                matched_skills += 1
        
        return round(matched_skills / len(all_required_skills), 2) if all_required_skills else 0.0

    async def get_career_insights(self, user_id: str) -> List[Dict]:
        """
        Get career insights for a user
        """
        try:
            result = supabase_client.table("career_insights").select("*").eq("user_id", user_id).order(
                "created_at", desc=True
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting career insights: {e}")
            return []

    async def update_learning_progress(
        self, 
        user_id: str, 
        skill_domain: str, 
        completed_skills: List[str]
    ) -> Dict:
        """
        Update learning progress for a user
        """
        try:
            # Get or create learning path
            result = supabase_client.table("learning_paths").select("*").eq("user_id", user_id).eq(
                "skill_domain", skill_domain
            ).execute()
            
            if result.data:
                learning_path = result.data[0]
                progress = learning_path.get("progress", {})
                
                # Update progress
                for skill in completed_skills:
                    progress[skill] = {
                        "completed": True,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                
                # Update database
                supabase_client.table("learning_paths").update({
                    "progress": progress,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", learning_path["id"]).execute()
                
                return {"success": True, "progress": progress}
            else:
                # Create new learning path
                new_path = {
                    "user_id": user_id,
                    "skill_domain": skill_domain,
                    "target_skills": [],
                    "progress": {skill: {"completed": True, "completed_at": datetime.utcnow().isoformat()} 
                               for skill in completed_skills},
                    "created_at": datetime.utcnow().isoformat()
                }
                
                result = supabase_client.table("learning_paths").insert(new_path).execute()
                return {"success": True, "learning_path_id": result.data[0]["id"] if result.data else None}
                
        except Exception as e:
            logger.error(f"Error updating learning progress: {e}")
            return {"error": str(e)}

# Global instance
career_advisor_service = CareerAdvisorService()