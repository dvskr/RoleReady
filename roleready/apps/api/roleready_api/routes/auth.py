from fastapi import APIRouter, Depends
from roleready_api.core.auth import require_user

router = APIRouter()

@router.get('/me')
async def me(auth = Depends(require_user)):
    return {"user_id": auth['user_id']}
