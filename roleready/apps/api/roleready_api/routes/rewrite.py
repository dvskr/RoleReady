from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class RewriteIn(BaseModel):
    section: str # "summary" | "experience"
    text: str
    jd_keywords: list[str] = []


@router.post("/rewrite")
async def rewrite(data: RewriteIn):
    # TODO: call LLM; return a mocked improvement for now
    improved = data.text + " — optimized for JD keywords: " + ", ".join(data.jd_keywords[:3])
    return {"rewritten": improved}