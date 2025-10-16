from supabase import create_client, Client
import os

# Initialize Supabase client only if credentials are available
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

def save_resume(user_id: str, content: str):
    """Save resume content to Supabase"""
    if not supabase:
        print("Supabase not configured - skipping save")
        return None
    try:
        result = supabase.table("resumes").insert({
            "user_id": user_id, 
            "content": content
        }).execute()
        return result
    except Exception as e:
        print(f"Error saving resume: {e}")
        return None

def get_resumes(user_id: str):
    """Get all resumes for a user"""
    if not supabase:
        print("Supabase not configured - returning empty list")
        return []
    try:
        result = supabase.table("resumes").select("*").eq("user_id", user_id).execute()
        return result.data
    except Exception as e:
        print(f"Error getting resumes: {e}")
        return []

async def save_analytics(user_id: str, resume_id: str, score: float, coverage: float, 
                        jd_keywords: list, missing_keywords: list, mode: str):
    """Save analytics data for tracking trends"""
    if not supabase:
        print("Supabase not configured - skipping analytics save")
        return None
    try:
        result = supabase.table("analytics").insert({
            "user_id": user_id,
            "resume_id": resume_id,
            "score": score,
            "coverage": coverage,
            "jd_keywords": jd_keywords,
            "missing_keywords": missing_keywords,
            "mode": mode
        }).execute()
        return result
    except Exception as e:
        print(f"Error saving analytics: {e}")
        return None

def get_analytics(user_id: str, limit: int = 50):
    """Get analytics data for a user"""
    if not supabase:
        print("Supabase not configured - returning empty list")
        return []
    try:
        result = supabase.table("analytics").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return []
