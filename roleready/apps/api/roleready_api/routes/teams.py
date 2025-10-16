"""
Team Management Routes
Handles team creation, member management, and team-based resume sharing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from roleready_api.core.auth import get_current_user
from roleready_api.core.supabase import get_supabase_client

router = APIRouter(prefix="/teams", tags=["Teams"])

# Pydantic models
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime
    member_count: int

class TeamMember(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    joined_at: Optional[datetime]
    invited_at: datetime

class TeamInvite(BaseModel):
    email: EmailStr
    role: str = "editor"  # owner, editor, viewer

class TeamMemberUpdate(BaseModel):
    role: str

# Dependency to get current user
async def get_current_user_dependency():
    user = await get_current_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Create a new team"""
    
    supabase = get_supabase_client()
    
    # Create team using the database function
    result = supabase.rpc("create_team", {
        "team_name": team_data.name,
        "team_description": team_data.description
    }).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )
    
    team_id = result.data
    
    # Get the created team details
    team_result = supabase.table("teams").select("*").eq("id", team_id).execute()
    team = team_result.data[0]
    
    # Get member count
    member_count_result = supabase.table("team_members").select("user_id", count="exact").eq("team_id", team_id).execute()
    member_count = member_count_result.count or 0
    
    return TeamResponse(
        id=team["id"],
        name=team["name"],
        description=team["description"],
        owner_id=team["owner_id"],
        created_at=datetime.fromisoformat(team["created_at"]),
        updated_at=datetime.fromisoformat(team["updated_at"]),
        member_count=member_count
    )

@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    current_user: dict = Depends(get_current_user_dependency)
):
    """List all teams the current user is a member of"""
    
    supabase = get_supabase_client()
    
    # Get teams where user is a member
    result = supabase.table("teams").select(
        "id, name, description, owner_id, created_at, updated_at"
    ).in_(
        "id",
        supabase.table("team_members").select("team_id").eq("user_id", current_user["id"])
    ).execute()
    
    teams = []
    for team in result.data:
        # Get member count for each team
        member_count_result = supabase.table("team_members").select("user_id", count="exact").eq("team_id", team["id"]).execute()
        member_count = member_count_result.count or 0
        
        teams.append(TeamResponse(
            id=team["id"],
            name=team["name"],
            description=team["description"],
            owner_id=team["owner_id"],
            created_at=datetime.fromisoformat(team["created_at"]),
            updated_at=datetime.fromisoformat(team["updated_at"]),
            member_count=member_count
        ))
    
    return teams

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get details of a specific team"""
    
    supabase = get_supabase_client()
    
    # Check if user is a member of the team
    membership_result = supabase.table("team_members").select("role").eq("team_id", team_id).eq("user_id", current_user["id"]).execute()
    
    if not membership_result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this team"
        )
    
    # Get team details
    team_result = supabase.table("teams").select("*").eq("id", team_id).execute()
    if not team_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = team_result.data[0]
    
    # Get member count
    member_count_result = supabase.table("team_members").select("user_id", count="exact").eq("team_id", team_id).execute()
    member_count = member_count_result.count or 0
    
    return TeamResponse(
        id=team["id"],
        name=team["name"],
        description=team["description"],
        owner_id=team["owner_id"],
        created_at=datetime.fromisoformat(team["created_at"]),
        updated_at=datetime.fromisoformat(team["updated_at"]),
        member_count=member_count
    )

@router.get("/{team_id}/members", response_model=List[TeamMember])
async def list_team_members(
    team_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """List all members of a team"""
    
    supabase = get_supabase_client()
    
    # Check if user is a member of the team
    membership_result = supabase.table("team_members").select("role").eq("team_id", team_id).eq("user_id", current_user["id"]).execute()
    
    if not membership_result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this team"
        )
    
    # Get team members with user details
    result = supabase.table("team_members").select(
        "user_id, role, invited_at, joined_at, auth.users(email, raw_user_meta_data)"
    ).eq("team_id", team_id).execute()
    
    members = []
    for member in result.data:
        user_data = member["auth.users"]
        members.append(TeamMember(
            user_id=member["user_id"],
            email=user_data["email"],
            name=user_data["raw_user_meta_data"].get("name", user_data["email"]),
            role=member["role"],
            joined_at=datetime.fromisoformat(member["joined_at"]) if member["joined_at"] else None,
            invited_at=datetime.fromisoformat(member["invited_at"])
        ))
    
    return members

@router.post("/{team_id}/invite")
async def invite_team_member(
    team_id: str,
    invite_data: TeamInvite,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Invite a user to join the team"""
    
    supabase = get_supabase_client()
    
    # Check if user is the team owner
    team_result = supabase.table("teams").select("owner_id").eq("id", team_id).execute()
    if not team_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if team_result.data[0]["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners can invite members"
        )
    
    # Validate role
    if invite_data.role not in ["owner", "editor", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'owner', 'editor', or 'viewer'"
        )
    
    # Use the database function to invite member
    result = supabase.rpc("invite_team_member", {
        "team_uuid": team_id,
        "user_email": invite_data.email,
        "member_role": invite_data.role
    }).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to invite user. User may not exist or already be a member."
        )
    
    return {"message": f"Invitation sent to {invite_data.email}"}

@router.put("/{team_id}/members/{user_id}")
async def update_team_member(
    team_id: str,
    user_id: str,
    member_data: TeamMemberUpdate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Update a team member's role"""
    
    supabase = get_supabase_client()
    
    # Check if current user is the team owner
    team_result = supabase.table("teams").select("owner_id").eq("id", team_id).execute()
    if not team_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if team_result.data[0]["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners can update member roles"
        )
    
    # Validate role
    if member_data.role not in ["owner", "editor", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'owner', 'editor', or 'viewer'"
        )
    
    # Update member role
    result = supabase.table("team_members").update({
        "role": member_data.role
    }).eq("team_id", team_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    return {"message": "Member role updated successfully"}

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Remove a member from the team"""
    
    supabase = get_supabase_client()
    
    # Check if current user is the team owner or the member themselves
    team_result = supabase.table("teams").select("owner_id").eq("id", team_id).execute()
    if not team_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    is_owner = team_result.data[0]["owner_id"] == current_user["id"]
    is_self = user_id == current_user["id"]
    
    if not (is_owner or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners can remove members, or members can leave themselves"
        )
    
    # Don't allow removing the last owner
    if is_owner and user_id == team_result.data[0]["owner_id"]:
        owner_count = supabase.table("team_members").select("user_id", count="exact").eq("team_id", team_id).eq("role", "owner").execute()
        if owner_count.count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the team"
            )
    
    # Remove member
    result = supabase.table("team_members").delete().eq("team_id", team_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    return {"message": "Member removed from team successfully"}

@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Delete a team (only team owner can do this)"""
    
    supabase = get_supabase_client()
    
    # Check if current user is the team owner
    team_result = supabase.table("teams").select("owner_id").eq("id", team_id).execute()
    if not team_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if team_result.data[0]["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners can delete teams"
        )
    
    # Delete team (cascade will handle members and related data)
    result = supabase.table("teams").delete().eq("id", team_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return {"message": "Team deleted successfully"}

@router.get("/{team_id}/analytics")
async def get_team_analytics(
    team_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get analytics for a team"""
    
    supabase = get_supabase_client()
    
    # Check if user is a member of the team
    membership_result = supabase.table("team_members").select("role").eq("team_id", team_id).eq("user_id", current_user["id"]).execute()
    
    if not membership_result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this team"
        )
    
    # Get team analytics using the database function
    result = supabase.rpc("get_team_analytics", {
        "p_team_id": team_id,
        "p_days": days
    }).execute()
    
    return {
        "team_id": team_id,
        "period_days": days,
        "analytics": result.data
    }
