from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from roleready_api.services.export_docx import build_docx
from roleready_api.services.export_tpl import build_docx_template, parse_resume_content
from io import BytesIO

router = APIRouter()

@router.post('/export/docx')
async def export_docx(title: str = Body("Resume"), content: str = Body(...)):
    data = build_docx(content, title)
    return StreamingResponse(
        BytesIO(data), 
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f'attachment; filename="{title.replace(" ", "_")}.docx"'
        }
    )

@router.post('/export/docx-template')
async def export_docx_template(payload: dict = Body(...)):
    """Export DOCX using template with structured data"""
    # payload example: {"template": "classic.docx", "content": "resume text", "title": "My Resume"}
    content = payload.get("content", "")
    template = payload.get("template", "classic.docx")
    title = payload.get("title", "Resume")
    
    # Parse content into structured data
    data = parse_resume_content(content)
    
    # Build DOCX from template
    blob = build_docx_template(data, template)
    
    return StreamingResponse(
        BytesIO(blob), 
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f'attachment; filename="{title.replace(" ", "_")}.docx"'
        }
    )
