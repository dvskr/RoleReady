"""
Job Description Analysis Service
Mock implementation for development
"""

from typing import Dict, List

async def analyze_job_description(jd_text: str) -> Dict:
    """
    Analyze job description text
    Mock implementation for development
    """
    # Extract keywords and requirements
    keywords = []
    requirements = []
    
    # Simple keyword extraction
    common_keywords = [
        "Python", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker",
        "Machine Learning", "AI", "Data Analysis", "Project Management",
        "Leadership", "Communication", "Problem Solving"
    ]
    
    jd_lower = jd_text.lower()
    for keyword in common_keywords:
        if keyword.lower() in jd_lower:
            keywords.append(keyword)
    
    # Extract requirements (simple heuristic)
    lines = jd_text.split('\n')
    for line in lines:
        if any(word in line.lower() for word in ['required', 'must have', 'should have', 'experience']):
            requirements.append(line.strip())
    
    return {
        "keywords": keywords,
        "requirements": requirements[:10],  # Limit to 10
        "analysis": {
            "technical_focus": "software_development" if any(tech in jd_lower for tech in ['python', 'javascript', 'java', 'react']) else "general",
            "experience_level": "senior" if 'senior' in jd_lower else "mid" if 'mid' in jd_lower else "junior",
            "industry": "technology" if any(tech in jd_lower for tech in ['software', 'tech', 'engineering']) else "general"
        }
    }

def alignment_score(resume_text: str, job_description: str) -> float:
    """
    Calculate alignment score between resume and job description
    Mock implementation for development
    """
    # Simple keyword-based alignment
    resume_words = set(resume_text.lower().split())
    job_words = set(job_description.lower().split())
    
    # Remove common words
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
    resume_words -= common_words
    job_words -= common_words
    
    # Calculate overlap
    if len(job_words) == 0:
        return 0.5
    
    overlap = len(resume_words & job_words)
    return overlap / len(job_words)

def top_keywords(text: str, n: int = 10) -> List[str]:
    """
    Extract top keywords from text
    Mock implementation for development
    """
    # Simple keyword extraction
    common_keywords = [
        "Python", "JavaScript", "Java", "React", "Node.js", "Angular", "Vue.js",
        "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Git", "GitHub", "GitLab", "Jenkins", "CI/CD",
        "Machine Learning", "AI", "Data Analysis", "Pandas", "NumPy",
        "HTML", "CSS", "Bootstrap", "Sass", "Less",
        "TypeScript", "GraphQL", "REST API", "Microservices",
        "Agile", "Scrum", "Project Management", "Leadership"
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in common_keywords:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords[:n]