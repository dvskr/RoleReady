from fastapi import APIRouter, UploadFile, File, HTTPException
from roleready_api.services.parsing import parse_any
from roleready_api.services.llm_repair import repair_resume_json

router = APIRouter()

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    try:
        data = await file.read()
        if len(data) > 16 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (16MB limit)")

        structure = parse_any(file.filename, data)

        # Build flat text
        resume_text = "\n".join([
            structure.get("summary",""),
            ", ".join(structure.get("skills",[])),
            "\n".join([b for b in structure.get("experience", [])]),
        ]).strip()

        # Low-confidence repair (optional)
        if structure.get("confidence", 0.0) < 0.6 and resume_text:
            repaired = repair_resume_json(resume_text, {
                "summary": structure.get("summary",""),
                "skills": structure.get("skills",[]),
                "experience": [{"bullet": b} for b in structure.get("experience",[])]
            })
            structure["summary"]   = repaired.get("summary","")
            structure["skills"]    = repaired.get("skills",[])
            structure["experience"]= [b["bullet"] for b in repaired.get("experience",[])]

            # recompute flat text
            resume_text = "\n".join([
                structure.get("summary",""),
                ", ".join(structure.get("skills",[])),
                "\n".join(structure.get("experience",[])),
            ]).strip()

        return {
            "filename": file.filename,
            "structure_json": structure,
            "resume_text": resume_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
