"""
Subscription Service for RoleReady
Handles subscription management with billing enforcement toggle
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..core.billing_config import billing_config, is_billing_enabled, is_beta_phase

logger = logging.getLogger(__name__)

@dataclass
class SubscriptionInfo:
    """Subscription information for a user"""
    user_id: str
    plan_name: str
    status: str  # 'active', 'inactive', 'cancelled', 'past_due'
    created_at: datetime
    updated_at: datetime
    trial_ends_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    stripe_subscription_id: Optional[str] = None

@dataclass
class UsageStats:
    """Usage statistics for a user"""
    user_id: str
    feature_name: str
    current_usage: int
    limit: int
    period_start: datetime
    period_end: datetime
    reset_date: datetime

class SubscriptionService:
    """Service for managing user subscriptions and feature access"""
    
    def __init__(self):
        self.usage_cache = {}  # In production, this would be Redis
    
    def get_user_subscription(self, user_id: str) -> SubscriptionInfo:
        """Get subscription information for a user"""
        
        # During beta phase, return a mock subscription
        if is_beta_phase():
            return SubscriptionInfo(
                user_id=user_id,
                plan_name='beta_free',
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now(),
                trial_ends_at=None,
                current_period_start=datetime.now(),
                current_period_end=datetime.now() + timedelta(days=365),  # Long beta period
                cancel_at_period_end=False,
                stripe_subscription_id=None
            )
        
        # In production, this would query the database
        # For now, return a mock subscription
        return SubscriptionInfo(
            user_id=user_id,
            plan_name='free',
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            trial_ends_at=None,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            cancel_at_period_end=False,
            stripe_subscription_id=None
        )
    
    def can_access_feature(self, user_id: str, feature_name: str) -> bool:
        """Check if user can access a specific feature"""
        
        # During beta phase, all features are accessible
        if is_beta_phase():
            return True
        
        # Get user's subscription
        subscription = self.get_user_subscription(user_id)
        
        # Check if feature is available in the plan
        return billing_config.can_access_feature(subscription.plan_name, feature_name)
    
    def get_feature_usage(self, user_id: str, feature_name: str) -> UsageStats:
        """Get usage statistics for a specific feature"""
        
        # During beta phase, return unlimited usage
        if is_beta_phase():
            return UsageStats(
                user_id=user_id,
                feature_name=feature_name,
                current_usage=0,
                limit=-1,  # Unlimited
                period_start=datetime.now(),
                period_end=datetime.now() + timedelta(days=30),
                reset_date=datetime.now() + timedelta(days=30)
            )
        
        # Get user's subscription
        subscription = self.get_user_subscription(user_id)
        
        # Get feature limit
        limit = billing_config.get_feature_limit(subscription.plan_name, feature_name)
        
        # In production, this would query actual usage from database
        # For now, return mock usage
        current_usage = self._get_mock_usage(user_id, feature_name)
        
        return UsageStats(
            user_id=user_id,
            feature_name=feature_name,
            current_usage=current_usage,
            limit=limit,
            period_start=subscription.current_period_start or datetime.now(),
            period_end=subscription.current_period_end or datetime.now() + timedelta(days=30),
            reset_date=subscription.current_period_end or datetime.now() + timedelta(days=30)
        )
    
    def check_feature_access(self, user_id: str, feature_name: str) -> Dict[str, Any]:
        """Check feature access and return detailed information"""
        
        can_access = self.can_access_feature(user_id, feature_name)
        usage_stats = self.get_feature_usage(user_id, feature_name)
        subscription = self.get_user_subscription(user_id)
        
        return {
            'can_access': can_access,
            'feature_name': feature_name,
            'plan_name': subscription.plan_name,
            'usage': {
                'current': usage_stats.current_usage,
                'limit': usage_stats.limit,
                'unlimited': usage_stats.limit == -1,
                'remaining': usage_stats.limit - usage_stats.current_usage if usage_stats.limit > 0 else -1
            },
            'subscription': {
                'status': subscription.status,
                'is_beta': subscription.plan_name == 'beta_free',
                'trial_active': subscription.trial_ends_at and subscription.trial_ends_at > datetime.now()
            },
            'billing_enabled': is_billing_enabled()
        }
    
    def record_feature_usage(self, user_id: str, feature_name: str, count: int = 1):
        """Record usage of a feature"""
        
        # During beta phase, still track usage for analytics
        if is_beta_phase():
            logger.info(f"Beta usage tracked: {user_id} used {feature_name} {count} times")
            return
        
        # In production, this would update the database
        # For now, update mock cache
        cache_key = f"{user_id}_{feature_name}"
        if cache_key not in self.usage_cache:
            self.usage_cache[cache_key] = 0
        self.usage_cache[cache_key] += count
        
        logger.info(f"Usage recorded: {user_id} used {feature_name} {count} times")
    
    def _get_mock_usage(self, user_id: str, feature_name: str) -> int:
        """Get mock usage data (in production, this would query database)"""
        cache_key = f"{user_id}_{feature_name}"
        return self.usage_cache.get(cache_key, 0)
    
    def get_upgrade_options(self, user_id: str) -> list[Dict[str, Any]]:
        """Get available upgrade options for a user"""
        
        current_subscription = self.get_user_subscription(user_id)
        current_plan = current_subscription.plan_name
        
        # During beta phase, show that billing will be introduced later
        if is_beta_phase():
            return [
                {
                    'plan_name': 'pro',
                    'name': 'Professional',
                    'description': 'Coming soon - Unlimited access for professionals',
                    'price': '$29/month',
                    'features': [
                        'Unlimited resume parsing',
                        'Unlimited rewriting',
                        'Advanced job matching',
                        'Career advisor',
                        'API access',
                        'Team collaboration',
                        'Multilingual support'
                    ],
                    'available': False,
                    'beta_note': 'Available after beta phase'
                }
            ]
        
        # In production, this would return actual upgrade options
        upgrade_options = []
        
        if current_plan == 'free':
            upgrade_options.append({
                'plan_name': 'pro',
                'name': 'Professional',
                'description': 'Unlimited access for professionals',
                'price': '$29/month',
                'features': [
                    'Unlimited resume parsing',
                    'Unlimited rewriting',
                    'Advanced job matching',
                    'Career advisor',
                    'API access (10K requests/month)',
                    'Team collaboration',
                    'Multilingual support'
                ],
                'available': True
            })
        
        if current_plan in ['free', 'pro']:
            upgrade_options.append({
                'plan_name': 'enterprise',
                'name': 'Enterprise',
                'description': 'Full enterprise features',
                'price': 'Contact sales',
                'features': [
                    'Everything in Professional',
                    'Unlimited API access',
                    'Custom integrations',
                    'Priority support',
                    'Advanced analytics',
                    'SSO integration',
                    'Custom branding'
                ],
                'available': True
            })
        
        return upgrade_options

# Global subscription service instance
subscription_service = SubscriptionService()

# Convenience functions
def get_user_subscription(user_id: str) -> SubscriptionInfo:
    """Get subscription information for a user"""
    return subscription_service.get_user_subscription(user_id)

def can_access_feature(user_id: str, feature_name: str) -> bool:
    """Check if user can access a specific feature"""
    return subscription_service.can_access_feature(user_id, feature_name)

def check_feature_access(user_id: str, feature_name: str) -> Dict[str, Any]:
    """Check feature access and return detailed information"""
    return subscription_service.check_feature_access(user_id, feature_name)

def record_feature_usage(user_id: str, feature_name: str, count: int = 1):
    """Record usage of a feature"""
    subscription_service.record_feature_usage(user_id, feature_name, count)

def get_upgrade_options(user_id: str) -> list[Dict[str, Any]]:
    """Get available upgrade options for a user"""
    return subscription_service.get_upgrade_options(user_id)
