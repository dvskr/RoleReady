"""
Resume Rewrite Service
Mock implementation for development
"""

from typing import Dict, List

async def rewrite_resume_section(
    resume_text: str, 
    section: str, 
    job_description: str = None, 
    style: str = "professional"
) -> Dict:
    """
    Rewrite a specific section of a resume
    Mock implementation for development
    """
    
    # Find the section in the resume
    original_text = extract_section_text(resume_text, section)
    
    if not original_text:
        return {
            "original_text": "",
            "improved_text": "",
            "improvements": ["Section not found in resume"],
            "confidence": 0.0
        }
    
    # Generate improved text based on section type
    improved_text = generate_improved_text(original_text, section, job_description, style)
    
    # Generate improvement list
    improvements = generate_improvements(original_text, improved_text, section)
    
    # Calculate confidence score
    confidence = calculate_confidence(original_text, improved_text, section)
    
    return {
        "original_text": original_text,
        "improved_text": improved_text,
        "improvements": improvements,
        "confidence": confidence
    }

def extract_section_text(resume_text: str, section: str) -> str:
    """
    Extract text for a specific section
    """
    lines = resume_text.split('\n')
    section_text = []
    in_section = False
    
    section_keywords = {
        "summary": ["summary", "profile", "about", "overview"],
        "experience": ["experience", "employment", "work history"],
        "skills": ["skills", "competencies", "technologies"],
        "education": ["education", "academic", "degree"]
    }
    
    keywords = section_keywords.get(section.lower(), [section.lower()])
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if this line starts a new section
        if any(keyword in line_lower for keyword in keywords) and len(line.strip()) < 50:
            in_section = True
            continue
        
        # If we're in the section, collect text until we hit another section
        if in_section:
            if line.strip() == "":
                continue
            # Check if this is a new section header (short line, no punctuation)
            if len(line.strip()) < 50 and not any(p in line for p in ['.', ',', ':', '-']):
                break
            section_text.append(line.strip())
    
    return '\n'.join(section_text)

def generate_improved_text(original_text: str, section: str, job_description: str, style: str) -> str:
    """
    Generate improved text for the section
    Mock implementation
    """
    if section.lower() == "summary":
        return f"""Professional {original_text.split()[0].lower()} with extensive experience in software development and team leadership. Proven track record of delivering high-quality solutions and driving technical innovation. Strong background in modern technologies and agile methodologies."""
    
    elif section.lower() == "experience":
        # Enhance experience bullet points
        lines = original_text.split('\n')
        improved_lines = []
        for line in lines:
            if line.strip():
                # Add quantifiable results if not present
                if not any(char.isdigit() for char in line):
                    line += " resulting in improved performance and user satisfaction"
                improved_lines.append(line)
        return '\n'.join(improved_lines)
    
    elif section.lower() == "skills":
        # Enhance skills section
        skills = original_text.split(',')
        enhanced_skills = []
        for skill in skills:
            skill = skill.strip()
            if skill and skill not in enhanced_skills:
                enhanced_skills.append(skill)
        
        # Add relevant skills if job description provided
        if job_description:
            jd_skills = ["Python", "JavaScript", "React", "AWS", "Docker"]
            for skill in jd_skills:
                if skill.lower() in job_description.lower() and skill not in enhanced_skills:
                    enhanced_skills.append(skill)
        
        return ', '.join(enhanced_skills)
    
    else:
        # Generic improvement
        return original_text + " with enhanced focus on results and achievements."

def generate_improvements(original_text: str, improved_text: str, section: str) -> List[str]:
    """
    Generate list of improvements made
    """
    improvements = []
    
    if section.lower() == "summary":
        improvements.extend([
            "Added quantifiable achievements",
            "Enhanced professional language",
            "Included relevant keywords"
        ])
    
    elif section.lower() == "experience":
        improvements.extend([
            "Added measurable results",
            "Improved action verbs",
            "Enhanced impact statements"
        ])
    
    elif section.lower() == "skills":
        improvements.extend([
            "Organized skills by category",
            "Added relevant technologies",
            "Removed outdated skills"
        ])
    
    else:
        improvements.append("Enhanced content clarity and impact")
    
    return improvements

def calculate_confidence(original_text: str, improved_text: str, section: str) -> float:
    """
    Calculate confidence score for the rewrite
    """
    base_confidence = 0.8
    
    # Increase confidence based on improvements
    if len(improved_text) > len(original_text):
        base_confidence += 0.1
    
    # Increase confidence for specific sections
    if section.lower() in ["summary", "experience"]:
        base_confidence += 0.05
    
    return min(base_confidence, 1.0)
