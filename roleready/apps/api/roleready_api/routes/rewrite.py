from fastapi import APIRouter
from pydantic import BaseModel
from roleready_api.services.rewrite_ai import rewrite_text

router = APIRouter()

class RewriteIn(BaseModel):
    section: str
    text: str
    jd_keywords: list[str]
    resume_skills: list[str] = []

@router.post("/rewrite")
async def rewrite(in_data: RewriteIn):
    rewritten = rewrite_text(in_data.section, in_data.text, in_data.jd_keywords, in_data.resume_skills)
    return {"rewritten": rewritten}