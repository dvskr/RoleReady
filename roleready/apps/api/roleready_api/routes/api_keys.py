"""
API Key Management Routes
Handles generation, management, and authentication of API keys for public API access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import secrets
import hashlib
from datetime import datetime, timedelta

from roleready_api.core.auth import get_current_user
from roleready_api.core.config import get_settings
from roleready_api.core.supabase import get_supabase_client

router = APIRouter(prefix="/api-keys", tags=["API Keys"])
security = HTTPBearer()

settings = get_settings()

# Pydantic models
class APIKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only returned on creation
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

class APIKeyListResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

class APIKeyUsage(BaseModel):
    endpoint: str
    method: str
    count: int
    last_used: datetime

# Dependency to get current user
async def get_current_user_dependency():
    user = await get_current_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# Dependency to authenticate API key
async def authenticate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate API key from Authorization header"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    supabase = get_supabase_client()
    
    # Hash the provided key for comparison (security best practice)
    key_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    
    # Check if API key exists and is valid
    result = supabase.table("api_keys").select("*").eq("key", credentials.credentials).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    api_key_data = result.data[0]
    
    # Check if key is expired
    if api_key_data.get("expires_at"):
        expires_at = datetime.fromisoformat(api_key_data["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired"
            )
    
    # Update last_used_at
    supabase.table("api_keys").update({
        "last_used_at": datetime.now().isoformat()
    }).eq("id", api_key_data["id"]).execute()
    
    return {
        "user_id": api_key_data["user_id"],
        "api_key_id": api_key_data["id"],
        "api_key": credentials.credentials
    }

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Create a new API key for the current user"""
    
    # Generate a secure API key
    api_key = secrets.token_hex(24)
    
    # Calculate expiration date if provided
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now() + timedelta(days=key_data.expires_days)
    
    supabase = get_supabase_client()
    
    # Insert API key into database
    result = supabase.table("api_keys").insert({
        "user_id": current_user["id"],
        "key": api_key,
        "name": key_data.name,
        "expires_at": expires_at.isoformat() if expires_at else None
    }).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )
    
    created_key = result.data[0]
    
    return APIKeyResponse(
        id=created_key["id"],
        name=created_key["name"],
        key=api_key,  # Only return the key on creation
        created_at=datetime.fromisoformat(created_key["created_at"]),
        expires_at=datetime.fromisoformat(created_key["expires_at"]) if created_key["expires_at"] else None,
        last_used_at=datetime.fromisoformat(created_key["last_used_at"]) if created_key["last_used_at"] else None
    )

@router.get("/", response_model=List[APIKeyListResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user_dependency)
):
    """List all API keys for the current user"""
    
    supabase = get_supabase_client()
    
    result = supabase.table("api_keys").select(
        "id, name, created_at, expires_at, last_used_at"
    ).eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
    
    return [
        APIKeyListResponse(
            id=key["id"],
            name=key["name"],
            created_at=datetime.fromisoformat(key["created_at"]),
            expires_at=datetime.fromisoformat(key["expires_at"]) if key["expires_at"] else None,
            last_used_at=datetime.fromisoformat(key["last_used_at"]) if key["last_used_at"] else None
        )
        for key in result.data
    ]

@router.get("/{key_id}/usage", response_model=List[APIKeyUsage])
async def get_api_key_usage(
    key_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get usage statistics for a specific API key"""
    
    supabase = get_supabase_client()
    
    # Verify ownership
    key_result = supabase.table("api_keys").select("user_id").eq("id", key_id).execute()
    if not key_result.data or key_result.data[0]["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Get usage statistics
    usage_result = supabase.table("api_usage").select(
        "endpoint, method, created_at"
    ).eq("api_key_id", key_id).order("created_at", desc=True).execute()
    
    # Aggregate usage by endpoint and method
    usage_stats = {}
    for usage in usage_result.data:
        key = f"{usage['method']} {usage['endpoint']}"
        if key not in usage_stats:
            usage_stats[key] = {
                "endpoint": usage["endpoint"],
                "method": usage["method"],
                "count": 0,
                "last_used": usage["created_at"]
            }
        usage_stats[key]["count"] += 1
        if usage["created_at"] > usage_stats[key]["last_used"]:
            usage_stats[key]["last_used"] = usage["created_at"]
    
    return [
        APIKeyUsage(
            endpoint=stats["endpoint"],
            method=stats["method"],
            count=stats["count"],
            last_used=datetime.fromisoformat(stats["last_used"])
        )
        for stats in usage_stats.values()
    ]

@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Delete an API key"""
    
    supabase = get_supabase_client()
    
    # Verify ownership and delete
    result = supabase.table("api_keys").delete().eq("id", key_id).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}

@router.post("/{key_id}/regenerate")
async def regenerate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Regenerate an existing API key (creates new key, keeps same metadata)"""
    
    supabase = get_supabase_client()
    
    # Verify ownership
    key_result = supabase.table("api_keys").select("*").eq("id", key_id).eq("user_id", current_user["id"]).execute()
    if not key_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Generate new key
    new_api_key = secrets.token_hex(24)
    
    # Update the key
    result = supabase.table("api_keys").update({
        "key": new_api_key,
        "created_at": datetime.now().isoformat()
    }).eq("id", key_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API key"
        )
    
    updated_key = result.data[0]
    
    return APIKeyResponse(
        id=updated_key["id"],
        name=updated_key["name"],
        key=new_api_key,  # Return the new key
        created_at=datetime.fromisoformat(updated_key["created_at"]),
        expires_at=datetime.fromisoformat(updated_key["expires_at"]) if updated_key["expires_at"] else None,
        last_used_at=datetime.fromisoformat(updated_key["last_used_at"]) if updated_key["last_used_at"] else None
    )
