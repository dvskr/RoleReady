from fastapi import APIRouter
from roleready_api.core.config import settings
from .upload import router as upload_router

router = APIRouter(prefix=settings.API_PREFIX)

# Include upload routes
router.include_router(upload_router, tags=["upload"])

@router.get("/")
async def api_root():
    return {"message": "Role Ready API v1.0.0"}

@router.get("/test")
async def test_endpoint():
    return {"message": "API is working correctly!", "status": "success"}
