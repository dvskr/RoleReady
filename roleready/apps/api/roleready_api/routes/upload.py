from fastapi import APIRouter, UploadFile, File, HTTPException
from roleready_api.core.config import settings
import aiofiles
import os

router = APIRouter()

@router.get("/")
async def api_root():
    return {"message": "Role Ready API v1.0.0"}

@router.get("/test")
async def test_endpoint():
    return {"message": "API is working correctly!", "status": "success"}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "message": f"File '{file.filename}' uploaded successfully!",
            "filename": file.filename,
            "size": len(content),
            "path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # For now, return basic file info as "parsed" content
        # In a real app, you'd process the file content here
        return {
            "message": f"File '{file.filename}' parsed successfully!",
            "filename": file.filename,
            "size": len(content),
            "parsed_content": f"This is a placeholder for parsed content of {file.filename}",
            "file_type": file.content_type,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse failed: {str(e)}")