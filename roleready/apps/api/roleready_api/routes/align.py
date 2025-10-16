from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Literal, List
from roleready_api.services.jd_analysis import alignment_score as tfidf_align
from roleready_api.services.semantic_align import best_alignments
from roleready_api.services.supabase_client import save_analytics

router = APIRouter()

class AlignIn(BaseModel):
    resume_text: str = Field(min_length=10)
    jd_text: str = Field(min_length=10)
    mode: Literal["semantic", "tfidf"] = "semantic"
    user_id: str = Field(default="", description="User ID for analytics tracking")
    resume_id: str = Field(default="", description="Resume ID for analytics tracking")

# Simple splitter for JD into lines/requirements
def _split_jd(text: str) -> List[str]:
    lines = [ln.strip(" •-*\t") for ln in text.splitlines()]
    lines = [ln for ln in lines if len(ln.split()) >= 3]
    return lines[:100]

# Extract plausible bullets from resume_text (fallback if not structured)
def _split_resume(text: str) -> List[str]:
    bullets = []
    cur = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln: continue
        if ln.endswith(".") and len(ln.split()) >= 5 and not cur:
            bullets.append(ln)
        else:
            cur.append(ln)
    if cur:
        bullets.append(" ".join(cur))
    return bullets[:200]

@router.post("/align")
async def align(data: AlignIn):
    if data.mode == "tfidf":
        res = tfidf_align(data.resume_text, data.jd_text)
        result = {"mode": "tfidf", **res}
    else:
        # semantic mode
        jd_lines = _split_jd(data.jd_text)
        resume_bullets = _split_resume(data.resume_text)
        res = best_alignments(resume_bullets, jd_lines)
        result = {"mode": "semantic", **res}
    
    # Save analytics if user_id and resume_id are provided
    if data.user_id and data.resume_id:
        try:
            # Calculate coverage
            missing_keywords = result.get("missing_keywords", [])
            jd_keywords = result.get("jd_keywords", [])
            coverage = 1.0 - (len(missing_keywords) / max(len(jd_keywords), 1))
            
            await save_analytics(
                user_id=data.user_id,
                resume_id=data.resume_id,
                score=result.get("score", 0.0),
                coverage=coverage,
                jd_keywords=jd_keywords,
                missing_keywords=missing_keywords,
                mode=data.mode
            )
        except Exception as e:
            print(f"Failed to save analytics: {e}")
    
    return result
