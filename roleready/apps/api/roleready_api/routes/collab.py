from fastapi import APIRouter, Body, Depends, HTTPException
from roleready_api.core.auth import require_user
from roleready_api.services.supabase_client import supabase
import os
import uuid
from typing import Optional

router = APIRouter()

@router.post("/invite")
async def invite_collaborator(
    data: dict = Body(...),
    auth = Depends(require_user)
):
    """Invite a collaborator to a resume"""
    resume_id = data.get("resume_id")
    email = data.get("email")
    role = data.get("role", "viewer")
    
    if not resume_id or not email:
        raise HTTPException(status_code=400, detail="resume_id and email are required")
    
    if role not in ["viewer", "commenter", "editor"]:
        raise HTTPException(status_code=400, detail="role must be viewer, commenter, or editor")
    
    # Check if user owns the resume
    resume_result = supabase.table("resumes").select("user_id").eq("id", resume_id).execute()
    if not resume_result.data or resume_result.data[0]["user_id"] != auth["user_id"]:
        raise HTTPException(status_code=403, detail="You don't own this resume")
    
    # Check if collaborator already exists
    existing = supabase.table("collaborators").select("*").eq("resume_id", resume_id).eq("invitee_email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Collaborator already invited")
    
    # Create invite
    invite_token = str(uuid.uuid4())
    result = supabase.table("collaborators").insert({
        "resume_id": resume_id,
        "inviter_id": auth["user_id"],
        "invitee_email": email,
        "role": role,
        "invite_token": invite_token
    }).execute()
    
    # In production: send email with link
    link = f"http://localhost:3000/accept?token={invite_token}"
    
    return {
        "message": f"Invite sent to {email}",
        "link": link,
        "collaborator_id": result.data[0]["id"]
    }

@router.post("/accept")
async def accept_invite(
    data: dict = Body(...),
    auth = Depends(require_user)
):
    """Accept a collaboration invite"""
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    # Find the invite
    invite_result = supabase.table("collaborators").select("*").eq("invite_token", token).execute()
    if not invite_result.data:
        raise HTTPException(status_code=404, detail="Invalid invite token")
    
    invite = invite_result.data[0]
    
    # Check if already accepted
    if invite["accepted"]:
        raise HTTPException(status_code=400, detail="Invite already accepted")
    
    # Update invite status
    supabase.table("collaborators").update({
        "accepted": True
    }).eq("id", invite["id"]).execute()
    
    return {"message": "Invite accepted successfully"}

@router.get("/collaborators/{resume_id}")
async def get_collaborators(
    resume_id: str,
    auth = Depends(require_user)
):
    """Get all collaborators for a resume"""
    # Check if user can access this resume
    resume_result = supabase.table("resumes").select("user_id").eq("id", resume_id).execute()
    if not resume_result.data:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_owner = resume_result.data[0]["user_id"]
    user_email = auth.get("email")
    
    # Check access - owner or collaborator
    if resume_owner != auth["user_id"]:
        # Check if user is a collaborator
        collab_result = supabase.table("collaborators").select("*").eq("resume_id", resume_id).eq("invitee_email", user_email).execute()
        if not collab_result.data or not collab_result.data[0]["accepted"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all collaborators
    result = supabase.table("collaborators").select("*, inviter:user_profiles!collaborators_inviter_id_fkey(*)").eq("resume_id", resume_id).execute()
    
    return {"collaborators": result.data}

@router.delete("/collaborators/{collaborator_id}")
async def remove_collaborator(
    collaborator_id: str,
    auth = Depends(require_user)
):
    """Remove a collaborator"""
    # Get the collaborator record
    collab_result = supabase.table("collaborators").select("*, resumes!collaborators_resume_id_fkey(*)").eq("id", collaborator_id).execute()
    if not collab_result.data:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    
    collab = collab_result.data[0]
    resume = collab["resumes"]
    
    # Check if user owns the resume
    if resume["user_id"] != auth["user_id"]:
        raise HTTPException(status_code=403, detail="Only resume owner can remove collaborators")
    
    # Delete the collaborator
    supabase.table("collaborators").delete().eq("id", collaborator_id).execute()
    
    return {"message": "Collaborator removed successfully"}

@router.get("/role/{resume_id}")
async def get_user_role(
    resume_id: str,
    auth = Depends(require_user)
):
    """Get the current user's role for a resume"""
    # Check if user owns the resume
    resume_result = supabase.table("resumes").select("user_id").eq("id", resume_id).execute()
    if not resume_result.data:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_owner = resume_result.data[0]["user_id"]
    
    if resume_owner == auth["user_id"]:
        return {"role": "owner"}
    
    # Check if user is a collaborator
    user_email = auth.get("email")
    collab_result = supabase.table("collaborators").select("role").eq("resume_id", resume_id).eq("invitee_email", user_email).eq("accepted", True).execute()
    
    if collab_result.data:
        return {"role": collab_result.data[0]["role"]}
    
    raise HTTPException(status_code=403, detail="No access to this resume")

@router.post("/check-access")
async def check_resume_access(
    data: dict = Body(...),
    auth = Depends(require_user)
):
    """Check if user has access to a resume and what role"""
    resume_id = data.get("resume_id")
    
    if not resume_id:
        raise HTTPException(status_code=400, detail="resume_id is required")
    
    try:
        role_response = await get_user_role(resume_id, auth)
        return {
            "has_access": True,
            "role": role_response["role"]
        }
    except HTTPException as e:
        if e.status_code == 403:
            return {
                "has_access": False,
                "role": None
            }
        raise e
