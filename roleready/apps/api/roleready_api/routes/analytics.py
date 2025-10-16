from fastapi import APIRouter
from pydantic import BaseModel, Field
from roleready_api.services.supabase_client import get_analytics
from typing import List, Dict, Any

router = APIRouter()

class AnalyticsIn(BaseModel):
    user_id: str = Field(..., description="User ID to get analytics for")
    limit: int = Field(default=50, description="Number of analytics records to return")

@router.post("/analytics")
async def get_user_analytics(data: AnalyticsIn):
    """Get analytics data for a user"""
    try:
        analytics_data = get_analytics(data.user_id, data.limit)
        
        # Format data for charts
        chart_data = []
        for record in reversed(analytics_data):  # Reverse to get chronological order
            chart_data.append({
                't': record['created_at'][:16],  # Format datetime for chart
                'score': record['score'],
                'coverage': record['coverage'] * 100,  # Convert to percentage
                'mode': record['mode']
            })
        
        return {
            'success': True,
            'data': chart_data,
            'total_records': len(analytics_data)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': [],
            'total_records': 0
        }
