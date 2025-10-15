from __future__ import annotations
from typing import Dict, List
import json, os
from pydantic import BaseModel, Field, ValidationError

# If you use the official OpenAI python client:
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Bullet(BaseModel):
    bullet: str = Field(min_length=5, max_length=600)

class ResumeSchema(BaseModel):
    summary: str = ""
    skills: List[str] = []
    experience: List[Bullet] = []

SYSTEM = (
 "You are a parser. Return ONLY JSON matching this schema: "
 '{"summary": string, "skills": [string], "experience": [{"bullet": string}]} '
 "Do not invent companies, dates, or numbers. Use only text given. "
 "Keep bullets as single sentences. No prose outside JSON."
)

def repair_resume_json(raw_text: str, partial: Dict) -> Dict:
    """
    Sends a compact prompt to the LLM to repair structure when low confidence.
    Validates JSON against Pydantic schema. Falls back to partial on error.
    """
    snippet = raw_text
    if len(snippet) > 6000:  # keep prompt small for latency/cost
        snippet = snippet[:6000]

    # Compose a prompt with minimal instructions
    user = (
        "RAW_RESUME_TEXT:\n" + snippet +
        "\n\nCURRENT_PARTIAL_JSON:\n" + json.dumps(partial, ensure_ascii=False) +
        "\n\nReturn ONLY valid JSON per schema."
    )

    # --- Call your LLM here. Pseudo-call shown below ---
    # resp = client.chat.completions.create(
    #   model="gpt-5-large",
    #   messages=[{"role":"system","content":SYSTEM},{"role":"user","content":user}],
    #   temperature=0.0
    # )
    # text = resp.choices[0].message.content.strip()

    # For now, show structure (replace with real call):
    text = json.dumps(partial)

    try:
        parsed = json.loads(text)
        validated = ResumeSchema(**parsed).model_dump()
        return validated
    except (json.JSONDecodeError, ValidationError):
        return partial
