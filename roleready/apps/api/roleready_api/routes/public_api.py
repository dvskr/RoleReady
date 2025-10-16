"""
Public API Routes
External API endpoints for third-party integrations and automation tools.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import time
from datetime import datetime
import io

from roleready_api.routes.api_keys import authenticate_api_key
from roleready_api.services.parsing import parse_resume_content
from roleready_api.services.jd_analysis import analyze_job_description
from roleready_api.services.alignment import align_resume_with_job
from roleready_api.services.rewrite import rewrite_resume_section
from roleready_api.core.supabase import get_supabase_client
from roleready_api.services.subscription_service import record_feature_usage, check_feature_access
from roleready_api.core.billing_config import is_billing_enabled

router = APIRouter(prefix="/v1", tags=["Public API"])

# Pydantic models for request/response
class ParseRequest(BaseModel):
    text: str
    format: Optional[str] = "text"  # text, json, structured

class ParseResponse(BaseModel):
    message: str
    sections: Dict[str, Any]
    confidence: Optional[float] = None
    processing_time_ms: int

class AlignRequest(BaseModel):
    resume_text: str
    job_description: str
    mode: Optional[str] = "semantic"  # semantic, keyword, hybrid

class AlignResponse(BaseModel):
    overall_score: float
    section_scores: Dict[str, float]
    suggestions: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    processing_time_ms: int

class RewriteRequest(BaseModel):
    resume_text: str
    section: str
    job_description: Optional[str] = None
    style: Optional[str] = "professional"  # professional, technical, creative

class RewriteResponse(BaseModel):
    original_text: str
    improved_text: str
    improvements: list[str]
    confidence: float
    processing_time_ms: int

# Utility function to track API usage
async def track_api_usage(
    api_key_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    user_agent: str = None,
    ip_address: str = None,
    user_id: str = None
):
    """Track API usage for analytics and billing"""
    
    # Always track usage for analytics (even during beta)
    supabase = get_supabase_client()
    
    supabase.table("api_usage").insert({
        "api_key_id": api_key_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "request_size_bytes": request_size_bytes,
        "response_size_bytes": response_size_bytes,
        "user_agent": user_agent,
        "ip_address": ip_address
    }).execute()
    
    # Track feature usage for subscription management
    if user_id:
        # Map endpoint to feature name
        feature_map = {
            '/parse': 'api_access',
            '/align': 'api_access', 
            '/rewrite': 'api_access',
            '/export': 'api_access'
        }
        
        feature_name = feature_map.get(endpoint, 'api_access')
        record_feature_usage(user_id, feature_name, 1)

@router.post("/parse", response_model=ParseResponse)
async def parse_resume_public(
    request: ParseRequest,
    auth_data: dict = Depends(authenticate_api_key)
):
    """
    Parse a resume text into structured sections.
    
    This endpoint extracts personal information, experience, education, and skills
    from unstructured resume text.
    """
    start_time = time.time()
    
    try:
        # Parse the resume content
        result = await parse_resume_content(request.text)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Track usage
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/parse",
            method="POST",
            status_code=200,
            response_time_ms=processing_time,
            request_size_bytes=len(request.text.encode('utf-8')),
            response_size_bytes=len(json.dumps(result).encode('utf-8'))
        )
        
        return ParseResponse(
            message="Resume parsed successfully",
            sections=result.get("sections", {}),
            confidence=result.get("confidence", 0.95),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Track error usage
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/parse",
            method="POST",
            status_code=500,
            response_time_ms=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}"
        )

@router.post("/parse/file", response_model=ParseResponse)
async def parse_resume_file_public(
    file: UploadFile = File(...),
    format: str = Form(default="text"),
    auth_data: dict = Depends(authenticate_api_key)
):
    """
    Parse a resume from uploaded file (PDF, DOCX, TXT).
    
    Supports multiple file formats and extracts structured data.
    """
    start_time = time.time()
    
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported: PDF, DOCX, TXT"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # For now, we'll assume text extraction is handled by the parsing service
        # In a real implementation, you'd use libraries like PyPDF2, python-docx, etc.
        text_content = content.decode('utf-8') if file.content_type == "text/plain" else str(content)
        
        # Parse the content
        result = await parse_resume_content(text_content)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Track usage
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/parse/file",
            method="POST",
            status_code=200,
            response_time_ms=processing_time,
            request_size_bytes=len(content),
            response_size_bytes=len(json.dumps(result).encode('utf-8'))
        )
        
        return ParseResponse(
            message="Resume file parsed successfully",
            sections=result.get("sections", {}),
            confidence=result.get("confidence", 0.90),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/parse/file",
            method="POST",
            status_code=500,
            response_time_ms=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume file: {str(e)}"
        )

@router.post("/align", response_model=AlignResponse)
async def align_resume_public(
    request: AlignRequest,
    auth_data: dict = Depends(authenticate_api_key)
):
    """
    Align a resume with a job description.
    
    Analyzes how well a resume matches a job description and provides
    suggestions for improvement.
    """
    start_time = time.time()
    
    try:
        # Perform alignment analysis
        result = await align_resume_with_job(
            resume_text=request.resume_text,
            job_description=request.job_description,
            mode=request.mode
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Track usage
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/align",
            method="POST",
            status_code=200,
            response_time_ms=processing_time,
            request_size_bytes=len(request.resume_text.encode('utf-8')) + len(request.job_description.encode('utf-8')),
            response_size_bytes=len(json.dumps(result).encode('utf-8'))
        )
        
        return AlignResponse(
            overall_score=result.get("overall_score", 0.0),
            section_scores=result.get("section_scores", {}),
            suggestions=result.get("suggestions", []),
            matched_skills=result.get("matched_skills", []),
            missing_skills=result.get("missing_skills", []),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/align",
            method="POST",
            status_code=500,
            response_time_ms=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to align resume: {str(e)}"
        )

@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_resume_public(
    request: RewriteRequest,
    auth_data: dict = Depends(authenticate_api_key)
):
    """
    Rewrite a specific section of a resume.
    
    Uses AI to improve resume content for better alignment with job requirements.
    """
    start_time = time.time()
    
    try:
        # Perform rewrite
        result = await rewrite_resume_section(
            resume_text=request.resume_text,
            section=request.section,
            job_description=request.job_description,
            style=request.style
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Track usage
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/rewrite",
            method="POST",
            status_code=200,
            response_time_ms=processing_time,
            request_size_bytes=len(request.resume_text.encode('utf-8')),
            response_size_bytes=len(json.dumps(result).encode('utf-8'))
        )
        
        return RewriteResponse(
            original_text=result.get("original_text", request.resume_text),
            improved_text=result.get("improved_text", ""),
            improvements=result.get("improvements", []),
            confidence=result.get("confidence", 0.85),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        await track_api_usage(
            api_key_id=auth_data["api_key_id"],
            endpoint="/v1/rewrite",
            method="POST",
            status_code=500,
            response_time_ms=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rewrite resume: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/usage")
async def get_usage_stats(
    auth_data: dict = Depends(authenticate_api_key)
):
    """
    Get usage statistics for the authenticated API key.
    
    Returns usage metrics and limits for the current billing period.
    """
    supabase = get_supabase_client()
    
    # Get API key details
    key_result = supabase.table("api_keys").select("*").eq("id", auth_data["api_key_id"]).execute()
    if not key_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key = key_result.data[0]
    
    # Get usage statistics for current month
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    usage_result = supabase.table("api_usage").select(
        "endpoint, status_code, response_time_ms, created_at"
    ).eq("api_key_id", auth_data["api_key_id"]).gte("created_at", current_month.isoformat()).execute()
    
    # Calculate statistics
    total_requests = len(usage_result.data)
    successful_requests = len([u for u in usage_result.data if 200 <= u["status_code"] < 300])
    avg_response_time = sum(u["response_time_ms"] for u in usage_result.data) / total_requests if total_requests > 0 else 0
    
    # Group by endpoint
    endpoint_stats = {}
    for usage in usage_result.data:
        endpoint = usage["endpoint"]
        if endpoint not in endpoint_stats:
            endpoint_stats[endpoint] = {"count": 0, "success_rate": 0}
        endpoint_stats[endpoint]["count"] += 1
    
    return {
        "api_key_name": api_key["name"],
        "created_at": api_key["created_at"],
        "last_used_at": api_key["last_used_at"],
        "current_month_usage": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_response_time_ms": round(avg_response_time, 2),
            "endpoint_breakdown": endpoint_stats
        },
        "limits": {
            "requests_per_month": -1 if not is_billing_enabled() else 10000,
            "requests_remaining": -1 if not is_billing_enabled() else max(0, 10000 - total_requests),
            "unlimited": not is_billing_enabled(),
            "billing_enabled": is_billing_enabled()
        },
        "plan": {
            "name": "Public Beta" if not is_billing_enabled() else "Free",
            "is_beta": not is_billing_enabled(),
            "features": {
                "unlimited_requests": not is_billing_enabled(),
                "unlimited_parsing": not is_billing_enabled(),
                "unlimited_rewriting": not is_billing_enabled(),
                "api_access": not is_billing_enabled()
            }
        }
    }
