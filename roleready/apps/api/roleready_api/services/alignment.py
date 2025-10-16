"""
Resume-Job Alignment Analysis Service
Mock implementation for development
"""

from typing import Dict, List
import re

async def align_resume_with_job(resume_text: str, job_description: str, mode: str = "semantic") -> Dict:
    """
    Analyze how well a resume matches a job description
    Mock implementation for development
    """
    
    # Extract skills from both texts
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    
    # Calculate matches
    matched_skills = list(set(resume_skills) & set(job_skills))
    missing_skills = list(set(job_skills) - set(resume_skills))
    
    # Calculate overall score
    if len(job_skills) == 0:
        overall_score = 0.5  # Default score if no skills found in JD
    else:
        overall_score = len(matched_skills) / len(job_skills)
    
    # Generate suggestions
    suggestions = []
    if overall_score < 0.5:
        suggestions.append("Consider adding more relevant technical skills")
    if len(missing_skills) > 0:
        suggestions.append(f"Add experience with: {', '.join(missing_skills[:3])}")
    if len(resume_skills) < 5:
        suggestions.append("Include more technical skills in your resume")
    
    # Section scores (mock)
    section_scores = {
        "skills": overall_score,
        "experience": min(overall_score + 0.1, 1.0),
        "education": 0.8,  # Mock education score
        "summary": 0.7     # Mock summary score
    }
    
    return {
        "overall_score": round(overall_score, 2),
        "section_scores": section_scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "suggestions": suggestions,
        "analysis_mode": mode
    }

def extract_skills(text: str) -> List[str]:
    """
    Extract technical skills from text
    """
    skills = []
    text_lower = text.lower()
    
    # Common technical skills
    skill_patterns = [
        "python", "javascript", "java", "react", "node.js", "angular", "vue.js",
        "sql", "mongodb", "postgresql", "mysql", "redis",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "git", "github", "gitlab", "jenkins", "ci/cd",
        "machine learning", "ai", "data analysis", "pandas", "numpy",
        "html", "css", "bootstrap", "sass", "less",
        "typescript", "graphql", "rest api", "microservices",
        "agile", "scrum", "project management", "leadership"
    ]
    
    for skill in skill_patterns:
        if skill in text_lower:
            skills.append(skill.title())
    
    return list(set(skills))  # Remove duplicates
