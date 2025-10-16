from fastapi import APIRouter, Body, Depends, HTTPException
from roleready_api.core.auth import require_user
from roleready_api.services.supabase_client import supabase
from openai import OpenAI
import os
import uuid
from typing import Optional

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/target")
async def create_targeted_resume(
    payload: dict = Body(...),
    auth = Depends(require_user)
):
    """Create a targeted version of a resume for a specific job description"""
    resume_text = payload.get("resume_text")
    jd_text = payload.get("jd_text")
    base_resume_id = payload.get("base_resume_id")
    title = payload.get("title", f"Targeted Resume - {payload.get('job_title', 'Job Application')}")
    
    if not resume_text or not jd_text:
        raise HTTPException(status_code=400, detail="resume_text and jd_text are required")
    
    # Check if user has access to base resume (if provided)
    if base_resume_id:
        resume_result = supabase.table("resumes").select("user_id").eq("id", base_resume_id).execute()
        if not resume_result.data:
            raise HTTPException(status_code=404, detail="Base resume not found")
        
        # Check access - owner or collaborator
        resume_owner = resume_result.data[0]["user_id"]
        user_email = auth.get("email")
        
        if resume_owner != auth["user_id"]:
            # Check if user is a collaborator
            collab_result = supabase.table("collaborators").select("*").eq("resume_id", base_resume_id).eq("invitee_email", user_email).eq("accepted", True).execute()
            if not collab_result.data:
                raise HTTPException(status_code=403, detail="Access denied to base resume")
    
    # Create targeted resume using OpenAI
    try:
        prompt = (
            "You are a professional resume strategist with expertise in ATS optimization. "
            "Your task is to rewrite the provided resume to perfectly align with the given job description. "
            "\n\nGuidelines:\n"
            "1. Match keywords and phrases from the job description naturally\n"
            "2. Emphasize relevant skills and experience that align with the role\n"
            "3. Use quantifiable achievements where possible\n"
            "4. Maintain truthful information - never fabricate experience\n"
            "5. Adjust tone to match the company culture (infer from JD)\n"
            "6. Prioritize the most relevant experience sections\n"
            "7. Use action verbs that match the job requirements\n"
            "8. Keep the same format and structure as the original\n"
            "\nReturn the optimized resume as plain text, maintaining professional formatting."
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"JOB DESCRIPTION:\n{jd_text}\n\nORIGINAL RESUME:\n{resume_text}"}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        targeted_resume = response.choices[0].message.content.strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating targeted resume: {str(e)}")
    
    # Save the targeted resume to database
    try:
        resume_data = {
            "user_id": auth["user_id"],
            "title": title,
            "content": targeted_resume,
            "parent_id": base_resume_id
        }
        
        result = supabase.table("resumes").insert(resume_data).execute()
        new_resume_id = result.data[0]["id"]
        
        # Track usage
        supabase.table("usage_tracking").insert({
            "user_id": auth["user_id"],
            "action": "create_targeted_resume",
            "resource_type": "resume",
            "resource_id": new_resume_id,
            "metadata": {
                "base_resume_id": base_resume_id,
                "job_title": payload.get("job_title"),
                "company": payload.get("company")
            }
        }).execute()
        
        return {
            "targeted_resume": targeted_resume,
            "resume_id": new_resume_id,
            "title": title
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving targeted resume: {str(e)}")

@router.get("/targeted/{base_resume_id}")
async def get_targeted_versions(
    base_resume_id: str,
    auth = Depends(require_user)
):
    """Get all targeted versions of a base resume"""
    # Check if user has access to base resume
    resume_result = supabase.table("resumes").select("user_id").eq("id", base_resume_id).execute()
    if not resume_result.data:
        raise HTTPException(status_code=404, detail="Base resume not found")
    
    resume_owner = resume_result.data[0]["user_id"]
    user_email = auth.get("email")
    
    if resume_owner != auth["user_id"]:
        # Check if user is a collaborator
        collab_result = supabase.table("collaborators").select("*").eq("resume_id", base_resume_id).eq("invitee_email", user_email).eq("accepted", True).execute()
        if not collab_result.data:
            raise HTTPException(status_code=403, detail="Access denied to base resume")
    
    # Get all targeted versions
    result = supabase.table("resumes").select("*").eq("parent_id", base_resume_id).order("created_at", desc=True).execute()
    
    return {"targeted_versions": result.data}

@router.post("/analyze-match")
async def analyze_jd_match(
    payload: dict = Body(...),
    auth = Depends(require_user)
):
    """Analyze how well a resume matches a job description"""
    resume_text = payload.get("resume_text")
    jd_text = payload.get("jd_text")
    
    if not resume_text or not jd_text:
        raise HTTPException(status_code=400, detail="resume_text and jd_text are required")
    
    try:
        prompt = (
            "You are a resume analysis expert. Analyze how well the provided resume matches the job description. "
            "Provide a detailed assessment with specific recommendations.\n\n"
            "Return a JSON response with the following structure:\n"
            "{\n"
            '  "match_score": 85,  // Score from 0-100\n'
            '  "strengths": ["List of strengths"],\n'
            '  "weaknesses": ["List of weaknesses"],\n'
            '  "missing_keywords": ["Important keywords missing"],\n'
            '  "recommendations": ["Specific improvement suggestions"],\n'
            '  "keyword_coverage": 75  // Percentage of JD keywords found\n'
            "}\n\n"
            "Be specific and actionable in your recommendations."
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"JOB DESCRIPTION:\n{jd_text}\n\nRESUME:\n{resume_text}"}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        analysis_text = response.choices[0].message.content.strip()
        
        # Try to parse as JSON, fallback to text if parsing fails
        try:
            import json
            analysis = json.loads(analysis_text)
        except:
            analysis = {
                "match_score": 75,
                "strengths": ["Resume shows relevant experience"],
                "weaknesses": ["Could better match job requirements"],
                "missing_keywords": [],
                "recommendations": ["Review job description for better alignment"],
                "keyword_coverage": 70,
                "raw_analysis": analysis_text
            }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume match: {str(e)}")
