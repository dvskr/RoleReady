from fastapi import APIRouter
from pydantic import BaseModel, Field
from roleready_api.services.jd_analysis import alignment_score

router = APIRouter()

class AlignIn(BaseModel):
    resume_text: str = Field(min_length=10)
    jd_text: str = Field(min_length=10)

@router.post("/align")
async def align(data: AlignIn):
    result = alignment_score(data.resume_text, data.jd_text)
    return {"score": result["score"], "missing_keywords": result["missing_keywords"], "jd_keywords": result["jd_keywords"]}
