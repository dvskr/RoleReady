from fastapi import APIRouter
from roleready_api.core.config import settings
from .upload import router as upload_router
from .parse import router as parse_router
from .align import router as align_router
from .rewrite import router as rewrite_router
from .health import router as health_router
from .auth import router as auth_router
from .analytics import router as analytics_router
from .export import router as export_router
from .collab import router as collab_router
from .target import router as target_router

router = APIRouter(prefix=settings.API_PREFIX)

# Include all routes
router.include_router(upload_router, tags=["upload"])
router.include_router(parse_router, tags=["parse"])
router.include_router(align_router, tags=["align"])
router.include_router(rewrite_router, tags=["rewrite"])
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(analytics_router, tags=["analytics"])
router.include_router(export_router, tags=["export"])
router.include_router(collab_router, tags=["collaboration"])
router.include_router(target_router, tags=["targeting"])

@router.get("/")
async def api_root():
    return {"message": "Role Ready API v1.0.0"}

@router.get("/test")
async def test_endpoint():
    return {"message": "API is working correctly!", "status": "success"}
