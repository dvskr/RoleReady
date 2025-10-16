"""
Feedback API Routes
Endpoints for collecting user feedback and providing insights for model improvement
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from roleready_api.core.auth import get_current_user
from roleready_api.services.feedback import (
    feedback_collector, 
    feedback_analyzer,
    record_user_feedback,
    get_feedback_insights
)

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Pydantic models
class FeedbackSubmission(BaseModel):
    resume_id: str
    old_text: str
    new_text: str
    feedback_type: str = Field(default="manual_edit", description="Type: manual_edit, rejection, improvement, rewrite")
    section: Optional[str] = Field(default=None, description="Resume section being edited")
    confidence_score: Optional[float] = Field(default=None, description="AI confidence score for original text")
    processing_time_ms: Optional[int] = Field(default=None, description="AI processing time")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (job description, etc.)")

class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str
    timestamp: datetime

class FeedbackInsights(BaseModel):
    total_feedback: int
    time_period_days: int
    feedback_by_type: Dict[str, int]
    feedback_by_section: Dict[str, int]
    common_patterns: Dict[str, float]
    model_performance: Dict[str, Any]
    recommendations: List[str]

class FeedbackHistory(BaseModel):
    id: str
    resume_id: str
    section: str
    feedback_type: str
    timestamp: datetime
    confidence_score: Optional[float]
    text_length_ratio: float

class ModelImprovement(BaseModel):
    type: str
    priority: str
    description: str
    impact: str
    implementation: str

# Dependency to get current user
async def get_current_user_dependency():
    user = await get_current_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackSubmission,
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Submit user feedback for model improvement
    
    This endpoint captures user edits and interactions to improve the AI model.
    Feedback is used to identify patterns and improve future suggestions.
    """
    
    try:
        # Validate feedback data
        if not feedback_data.old_text.strip() or not feedback_data.new_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both old_text and new_text are required"
            )
        
        if feedback_data.feedback_type not in ['manual_edit', 'rejection', 'improvement', 'rewrite']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid feedback_type. Must be one of: manual_edit, rejection, improvement, rewrite"
            )
        
        # Record feedback
        feedback_id = await record_user_feedback(
            user_id=current_user["id"],
            resume_id=feedback_data.resume_id,
            old_text=feedback_data.old_text,
            new_text=feedback_data.new_text,
            feedback_type=feedback_data.feedback_type,
            section=feedback_data.section,
            team_id=feedback_data.context.get('team_id') if feedback_data.context else None,
            confidence_score=feedback_data.confidence_score,
            processing_time_ms=feedback_data.processing_time_ms,
            context=feedback_data.context
        )
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message="Feedback submitted successfully",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/insights", response_model=FeedbackInsights)
async def get_insights(
    time_period_days: int = 30,
    section: Optional[str] = None,
    feedback_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get feedback insights and model performance metrics
    
    Provides analysis of user feedback patterns and recommendations for model improvement.
    """
    
    try:
        insights = await get_feedback_insights(
            time_period_days=time_period_days,
            section=section,
            feedback_type=feedback_type
        )
        
        return FeedbackInsights(**insights)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )

@router.get("/history", response_model=List[FeedbackHistory])
async def get_feedback_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get feedback history for the current user
    
    Returns a list of recent feedback submissions by the user.
    """
    
    try:
        history = await feedback_analyzer.get_user_feedback_history(
            user_id=current_user["id"],
            limit=limit
        )
        
        return [
            FeedbackHistory(
                id=item["id"],
                resume_id=item["resume_id"],
                section=item["section"],
                feedback_type=item["feedback_type"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                confidence_score=item["confidence_score"],
                text_length_ratio=item["text_length_ratio"]
            )
            for item in history
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback history: {str(e)}"
        )

@router.get("/improvements", response_model=List[ModelImprovement])
async def get_model_improvements(
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get model improvement recommendations based on feedback analysis
    
    Returns prioritized recommendations for improving the AI model based on user feedback patterns.
    """
    
    try:
        improvements = await feedback_analyzer.generate_model_improvements()
        
        return [
            ModelImprovement(
                type=item["type"],
                priority=item["priority"],
                description=item["description"],
                impact=item["impact"],
                implementation=item["implementation"]
            )
            for item in improvements
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model improvements: {str(e)}"
        )

@router.get("/patterns/{section}")
async def get_section_patterns(
    section: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get feedback patterns for a specific resume section
    
    Analyzes user feedback patterns for a specific section (summary, experience, skills, etc.)
    to identify common improvement areas.
    """
    
    try:
        # Mock section-specific patterns
        patterns = {
            "summary": {
                "common_issues": [
                    "Too generic or vague",
                    "Lacks specific achievements",
                    "Missing quantifiable results"
                ],
                "user_preferences": [
                    "Specific metrics and numbers",
                    "Industry-relevant keywords",
                    "Concise but impactful language"
                ],
                "improvement_suggestions": [
                    "Add quantified achievements",
                    "Include relevant industry terms",
                    "Focus on unique value proposition"
                ]
            },
            "experience": {
                "common_issues": [
                    "Bullet points too generic",
                    "Missing action verbs",
                    "No measurable outcomes"
                ],
                "user_preferences": [
                    "Strong action verbs",
                    "Quantified results",
                    "Technical details"
                ],
                "improvement_suggestions": [
                    "Use specific metrics",
                    "Include technical skills used",
                    "Show business impact"
                ]
            },
            "skills": {
                "common_issues": [
                    "Outdated technologies",
                    "Too many soft skills",
                    "Missing relevant tools"
                ],
                "user_preferences": [
                    "Current technologies",
                    "Industry-standard tools",
                    "Proficiency levels"
                ],
                "improvement_suggestions": [
                    "Update to current tech stack",
                    "Add relevant certifications",
                    "Include proficiency indicators"
                ]
            }
        }
        
        section_patterns = patterns.get(section.lower(), {
            "common_issues": ["Generic content", "Lacks specificity"],
            "user_preferences": ["Specific details", "Relevant keywords"],
            "improvement_suggestions": ["Add more detail", "Use specific language"]
        })
        
        return {
            "section": section,
            "patterns": section_patterns,
            "total_feedback": 45,  # Mock number
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section patterns: {str(e)}"
        )

@router.post("/batch")
async def submit_batch_feedback(
    feedback_list: List[FeedbackSubmission],
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Submit multiple feedback records in batch
    
    Efficiently process multiple feedback submissions at once.
    """
    
    try:
        if len(feedback_list) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 100 feedback records"
            )
        
        feedback_ids = []
        for feedback_data in feedback_list:
            feedback_id = await record_user_feedback(
                user_id=current_user["id"],
                resume_id=feedback_data.resume_id,
                old_text=feedback_data.old_text,
                new_text=feedback_data.new_text,
                feedback_type=feedback_data.feedback_type,
                section=feedback_data.section,
                team_id=feedback_data.context.get('team_id') if feedback_data.context else None,
                confidence_score=feedback_data.confidence_score,
                processing_time_ms=feedback_data.processing_time_ms,
                context=feedback_data.context
            )
            feedback_ids.append(feedback_id)
        
        return {
            "message": f"Successfully submitted {len(feedback_ids)} feedback records",
            "feedback_ids": feedback_ids,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit batch feedback: {str(e)}"
        )

@router.get("/stats")
async def get_feedback_stats(
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get feedback statistics for the current user
    
    Returns summary statistics about the user's feedback contributions.
    """
    
    try:
        # Mock user statistics
        stats = {
            "user_id": current_user["id"],
            "total_feedback_submitted": 25,
            "feedback_by_type": {
                "manual_edit": 12,
                "improvement": 8,
                "rejection": 3,
                "rewrite": 2
            },
            "feedback_by_section": {
                "summary": 8,
                "experience": 10,
                "skills": 4,
                "education": 2,
                "other": 1
            },
            "average_confidence_score": 0.72,
            "most_common_improvements": [
                "Added quantified metrics",
                "Improved action verbs",
                "Added technical details"
            ],
            "contribution_score": 85,  # Out of 100
            "last_feedback_date": (datetime.now() - timedelta(days=2)).isoformat()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {str(e)}"
        )
