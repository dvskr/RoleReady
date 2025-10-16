"""
Subscription Routes for RoleReady
Handles subscription information and billing status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

from ..core.auth import require_user
from ..services.subscription_service import (
    get_user_subscription, 
    check_feature_access, 
    get_upgrade_options,
    subscription_service
)
from ..core.billing_config import get_plan_display_info, is_billing_enabled, is_beta_phase

router = APIRouter(prefix="/subscription", tags=["Subscription"])

class SubscriptionResponse(BaseModel):
    user_id: str
    plan_name: str
    plan_display_name: str
    status: str
    is_beta: bool
    is_unlimited: bool
    billing_enabled: bool
    created_at: str
    current_period_end: str
    features: Dict[str, Any]

class FeatureAccessResponse(BaseModel):
    feature_name: str
    can_access: bool
    usage: Dict[str, Any]
    plan_info: Dict[str, Any]

class UpgradeOption(BaseModel):
    plan_name: str
    name: str
    description: str
    price: str
    features: List[str]
    available: bool
    beta_note: str = None

@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(user_data: dict = Depends(require_user)):
    """Get current subscription status for the authenticated user"""
    
    user_id = user_data["user_id"]
    
    # Get subscription info
    subscription = get_user_subscription(user_id)
    plan_display_info = get_plan_display_info(subscription.plan_name)
    
    return SubscriptionResponse(
        user_id=user_id,
        plan_name=subscription.plan_name,
        plan_display_name=plan_display_info["display_name"],
        status=subscription.status,
        is_beta=subscription.plan_name == 'beta_free',
        is_unlimited=plan_display_info["is_unlimited"],
        billing_enabled=is_billing_enabled(),
        created_at=subscription.created_at.isoformat(),
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        features={
            "resume_parsing": check_feature_access(user_id, "resume_parsing"),
            "resume_rewriting": check_feature_access(user_id, "resume_rewriting"),
            "job_matching": check_feature_access(user_id, "job_matching"),
            "career_advisor": check_feature_access(user_id, "career_advisor"),
            "api_access": check_feature_access(user_id, "api_access"),
            "team_collaboration": check_feature_access(user_id, "team_collaboration"),
            "multilingual": check_feature_access(user_id, "multilingual"),
            "export_formats": check_feature_access(user_id, "export_formats")
        }
    )

@router.get("/feature/{feature_name}", response_model=FeatureAccessResponse)
async def check_feature_access_endpoint(
    feature_name: str,
    user_data: dict = Depends(require_user)
):
    """Check access to a specific feature"""
    
    user_id = user_data["user_id"]
    access_info = check_feature_access(user_id, feature_name)
    
    return FeatureAccessResponse(
        feature_name=feature_name,
        can_access=access_info["can_access"],
        usage=access_info["usage"],
        plan_info=access_info["subscription"]
    )

@router.get("/upgrade-options", response_model=List[UpgradeOption])
async def get_upgrade_options_endpoint(user_data: dict = Depends(require_user)):
    """Get available upgrade options for the user"""
    
    user_id = user_data["user_id"]
    options = get_upgrade_options(user_id)
    
    return [
        UpgradeOption(
            plan_name=option["plan_name"],
            name=option["name"],
            description=option["description"],
            price=option["price"],
            features=option["features"],
            available=option["available"],
            beta_note=option.get("beta_note")
        )
        for option in options
    ]

@router.get("/billing-status")
async def get_billing_status():
    """Get overall billing system status"""
    
    return {
        "billing_enabled": is_billing_enabled(),
        "beta_phase": is_beta_phase(),
        "current_plan": "Public Beta" if is_beta_phase() else "Free",
        "message": "RoleReady is currently in public beta with free access to all features" if is_beta_phase() else "Billing system is active",
        "features": {
            "all_unlimited": is_beta_phase(),
            "no_restrictions": is_beta_phase(),
            "free_access": is_beta_phase()
        }
    }

@router.post("/usage/{feature_name}")
async def record_usage_endpoint(
    feature_name: str,
    count: int = 1,
    user_data: dict = Depends(require_user)
):
    """Record usage of a feature (for analytics during beta)"""
    
    user_id = user_data["user_id"]
    subscription_service.record_feature_usage(user_id, feature_name, count)
    
    return {
        "message": f"Usage recorded: {feature_name} used {count} times",
        "feature_name": feature_name,
        "count": count,
        "user_id": user_id,
        "beta_mode": is_beta_phase()
    }
