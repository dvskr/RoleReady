"""
Step 10 Features API Routes
Multilingual support, career advisor, recruiter matching, and enterprise features
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, List, Optional
import logging
from roleready_api.core.auth import get_current_user
from roleready_api.services.feedback import feedback_service
from roleready_api.services.career_advisor import career_advisor_service
from roleready_api.services.recruiter_matching import recruiter_matching_service
from roleready_api.services.multilingual import multilingual_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/step10", tags=["Step 10 Features"])

# Feedback Collection Routes
@router.post("/feedback")
async def collect_feedback(
    resume_id: str = Body(...),
    source: str = Body(...),
    suggestion: str = Body(...),
    final: str = Body(...),
    accepted: bool = Body(...),
    confidence_score: Optional[float] = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Collect feedback on AI suggestions for continuous learning"""
    try:
        result = await feedback_service.collect_feedback(
            user_id=current_user["id"],
            resume_id=resume_id,
            source=source,
            suggestion=suggestion,
            final=final,
            accepted=accepted,
            confidence_score=confidence_score
        )
        
        if result["success"]:
            return {"message": "Feedback collected successfully", "feedback_id": result["feedback_id"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error collecting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/stats")
async def get_feedback_stats(current_user: dict = Depends(get_current_user)):
    """Get feedback statistics for the current user"""
    try:
        stats = await feedback_service.get_feedback_stats(current_user["id"])
        return stats
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/export")
async def export_feedback_for_training(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Export anonymized feedback data for model training (admin only)"""
    # TODO: Add admin role check
    try:
        feedback_data = await feedback_service.export_feedback_for_training(days_back)
        return {
            "feedback_count": len(feedback_data),
            "feedback_data": feedback_data,
            "period_days": days_back
        }
        
    except Exception as e:
        logger.error(f"Error exporting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Career Advisor Routes
@router.post("/advisor")
async def analyze_career_path(
    resume_id: str = Body(...),
    resume_content: Dict = Body(...),
    target_domain: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Analyze career path and provide skill gap recommendations"""
    try:
        analysis = await career_advisor_service.analyze_career_path(
            user_id=current_user["id"],
            resume_id=resume_id,
            resume_content=resume_content,
            target_domain=target_domain
        )
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing career path: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/advisor/insights")
async def get_career_insights(current_user: dict = Depends(get_current_user)):
    """Get career insights for the current user"""
    try:
        insights = await career_advisor_service.get_career_insights(current_user["id"])
        return {"insights": insights}
        
    except Exception as e:
        logger.error(f"Error getting career insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/advisor/progress")
async def update_learning_progress(
    skill_domain: str = Body(...),
    completed_skills: List[str] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Update learning progress for completed skills"""
    try:
        result = await career_advisor_service.update_learning_progress(
            user_id=current_user["id"],
            skill_domain=skill_domain,
            completed_skills=completed_skills
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating learning progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Recruiter and Enterprise Routes
@router.post("/recruiter/jobs")
async def create_job_description(
    team_id: str = Body(...),
    title: str = Body(...),
    description: str = Body(...),
    requirements: Optional[List[str]] = Body(None),
    skills: Optional[List[str]] = Body(None),
    location: Optional[str] = Body(None),
    salary_range: Optional[Dict] = Body(None),
    experience_level: Optional[str] = Body(None),
    job_type: str = Body("full-time"),
    remote_friendly: bool = Body(False),
    current_user: dict = Depends(get_current_user)
):
    """Create a new job description"""
    try:
        result = await recruiter_matching_service.create_job_description(
            team_id=team_id,
            title=title,
            description=description,
            requirements=requirements,
            skills=skills,
            location=location,
            salary_range=salary_range,
            experience_level=experience_level,
            job_type=job_type,
            remote_friendly=remote_friendly,
            created_by=current_user["id"]
        )
        
        if result["success"]:
            return {"message": "Job description created successfully", "job": result["job"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error creating job description: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/recruiter/jobs/batch")
async def batch_upload_jobs(
    team_id: str = Body(...),
    jobs_data: List[Dict] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Batch upload multiple job descriptions"""
    try:
        result = await recruiter_matching_service.batch_upload_jobs(
            team_id=team_id,
            jobs_data=jobs_data,
            created_by=current_user["id"]
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/recruiter/match/{job_description_id}")
async def find_candidates(
    job_description_id: int,
    limit: int = Body(50),
    min_score: float = Body(0.3),
    current_user: dict = Depends(get_current_user)
):
    """Find matching candidates for a job description"""
    try:
        candidates = await recruiter_matching_service.find_candidates(
            job_description_id=job_description_id,
            limit=limit,
            min_score=min_score
        )
        
        return {
            "candidates": candidates,
            "count": len(candidates),
            "job_id": job_description_id
        }
        
    except Exception as e:
        logger.error(f"Error finding candidates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/recruiter/matches/{match_id}")
async def update_match_status(
    match_id: int,
    status: str = Body(...),
    notes: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Update the status of a candidate match"""
    try:
        result = await recruiter_matching_service.update_match_status(
            match_id=match_id,
            status=status,
            reviewed_by=current_user["id"],
            notes=notes
        )
        
        if result["success"]:
            return {"message": "Match status updated successfully", "match": result["match"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error updating match status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/recruiter/analytics/{team_id}")
async def get_team_analytics(
    team_id: str,
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get recruiting analytics for a team"""
    try:
        analytics = await recruiter_matching_service.get_team_analytics(
            team_id=team_id,
            days_back=days_back
        )
        
        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting team analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Multilingual Support Routes
@router.post("/multilingual/detect")
async def detect_language(text: str = Body(...)):
    """Detect the language of the given text"""
    try:
        language = multilingual_service.detect_language(text)
        language_name = multilingual_service.get_language_name(language)
        
        return {
            "language": language,
            "language_name": language_name,
            "supported": multilingual_service.is_supported_language(language)
        }
        
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/multilingual/translate")
async def translate_text(
    text: str = Body(...),
    target_language: str = Body("en"),
    source_language: str = Body("auto")
):
    """Translate text to target language"""
    try:
        translated = multilingual_service.translate_text(text, target_language, source_language)
        
        return {
            "original_text": text,
            "translated_text": translated,
            "source_language": source_language,
            "target_language": target_language
        }
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/multilingual/supported")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": multilingual_service.supported_languages,
        "translation_mappings": multilingual_service.translation_mappings
    }

# Model Performance Routes
@router.get("/model/performance")
async def get_model_performance(current_user: dict = Depends(get_current_user)):
    """Get overall model performance metrics (admin only)"""
    # TODO: Add admin role check
    try:
        metrics = await feedback_service.get_model_performance_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/feedback/cleanup")
async def cleanup_old_feedback(
    days_to_keep: int = Query(90, ge=30, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Clean up old feedback data (admin only)"""
    # TODO: Add admin role check
    try:
        deleted_count = await feedback_service.cleanup_old_feedback(days_to_keep)
        return {
            "message": f"Cleaned up {deleted_count} old feedback records",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")