"""
Billing Configuration for RoleReady
Controls billing enforcement and feature access during beta phase
"""

import os
from typing import Dict, Any

class BillingConfig:
    """
    Centralized billing configuration that can be easily toggled
    """
    
    # Master toggle for billing enforcement
    BILLING_ENABLED = os.getenv('ROLEREADY_BILLING_ENABLED', 'false').lower() == 'true'
    
    # Beta phase settings
    BETA_PHASE = not BILLING_ENABLED
    
    # Plan configurations
    PLANS = {
        'beta_free': {
            'name': 'Public Beta',
            'description': 'Free access during beta phase',
            'features': {
                'resume_parsing': {'limit': -1, 'unlimited': True},
                'resume_rewriting': {'limit': -1, 'unlimited': True},
                'job_matching': {'limit': -1, 'unlimited': True},
                'career_advisor': {'limit': -1, 'unlimited': True},
                'api_access': {'limit': -1, 'unlimited': True},
                'team_collaboration': {'limit': -1, 'unlimited': True},
                'multilingual': {'limit': -1, 'unlimited': True},
                'export_formats': {'limit': -1, 'unlimited': True}
            },
            'display_name': 'Public Beta — Free access (no limits)',
            'color': 'green',
            'badge_text': 'BETA'
        },
        'free': {
            'name': 'Free',
            'description': 'Limited free tier',
            'features': {
                'resume_parsing': {'limit': 5, 'unlimited': False},
                'resume_rewriting': {'limit': 3, 'unlimited': False},
                'job_matching': {'limit': 2, 'unlimited': False},
                'career_advisor': {'limit': 1, 'unlimited': False},
                'api_access': {'limit': 100, 'unlimited': False},
                'team_collaboration': {'limit': 0, 'unlimited': False},
                'multilingual': {'limit': 0, 'unlimited': False},
                'export_formats': {'limit': 1, 'unlimited': False}
            },
            'display_name': 'Free Plan',
            'color': 'blue',
            'badge_text': 'FREE'
        },
        'pro': {
            'name': 'Professional',
            'description': 'Unlimited access for professionals',
            'features': {
                'resume_parsing': {'limit': -1, 'unlimited': True},
                'resume_rewriting': {'limit': -1, 'unlimited': True},
                'job_matching': {'limit': -1, 'unlimited': True},
                'career_advisor': {'limit': -1, 'unlimited': True},
                'api_access': {'limit': 10000, 'unlimited': False},
                'team_collaboration': {'limit': -1, 'unlimited': True},
                'multilingual': {'limit': -1, 'unlimited': True},
                'export_formats': {'limit': -1, 'unlimited': True}
            },
            'display_name': 'Professional Plan',
            'color': 'purple',
            'badge_text': 'PRO'
        },
        'enterprise': {
            'name': 'Enterprise',
            'description': 'Full enterprise features',
            'features': {
                'resume_parsing': {'limit': -1, 'unlimited': True},
                'resume_rewriting': {'limit': -1, 'unlimited': True},
                'job_matching': {'limit': -1, 'unlimited': True},
                'career_advisor': {'limit': -1, 'unlimited': True},
                'api_access': {'limit': -1, 'unlimited': True},
                'team_collaboration': {'limit': -1, 'unlimited': True},
                'multilingual': {'limit': -1, 'unlimited': True},
                'export_formats': {'limit': -1, 'unlimited': True}
            },
            'display_name': 'Enterprise Plan',
            'color': 'gold',
            'badge_text': 'ENTERPRISE'
        }
    }
    
    # Default plan during beta
    DEFAULT_PLAN = 'beta_free' if BETA_PHASE else 'free'
    
    @classmethod
    def get_plan_config(cls, plan_name: str = None) -> Dict[str, Any]:
        """Get configuration for a specific plan"""
        if plan_name is None:
            plan_name = cls.DEFAULT_PLAN
        
        return cls.PLANS.get(plan_name, cls.PLANS['free'])
    
    @classmethod
    def can_access_feature(cls, plan_name: str, feature_name: str) -> bool:
        """Check if a plan can access a specific feature"""
        if not cls.BILLING_ENABLED:
            return True  # All features free during beta
        
        plan_config = cls.get_plan_config(plan_name)
        feature_config = plan_config['features'].get(feature_name, {'limit': 0, 'unlimited': False})
        
        return feature_config['unlimited'] or feature_config['limit'] > 0
    
    @classmethod
    def get_feature_limit(cls, plan_name: str, feature_name: str) -> int:
        """Get the limit for a specific feature in a plan"""
        if not cls.BILLING_ENABLED:
            return -1  # Unlimited during beta
        
        plan_config = cls.get_plan_config(plan_name)
        feature_config = plan_config['features'].get(feature_name, {'limit': 0, 'unlimited': False})
        
        if feature_config['unlimited']:
            return -1
        
        return feature_config['limit']
    
    @classmethod
    def get_user_plan(cls, user_id: str = None) -> str:
        """Get the plan for a user (mock implementation)"""
        # In production, this would query the database
        # For now, return the default plan
        return cls.DEFAULT_PLAN
    
    @classmethod
    def get_plan_display_info(cls, plan_name: str = None) -> Dict[str, Any]:
        """Get display information for a plan"""
        if plan_name is None:
            plan_name = cls.get_user_plan()
        
        plan_config = cls.get_plan_config(plan_name)
        return {
            'name': plan_config['name'],
            'description': plan_config['description'],
            'display_name': plan_config['display_name'],
            'color': plan_config['color'],
            'badge_text': plan_config['badge_text'],
            'is_beta': plan_name == 'beta_free',
            'is_unlimited': all(
                feature['unlimited'] or feature['limit'] == -1
                for feature in plan_config['features'].values()
            )
        }

# Global billing config instance
billing_config = BillingConfig()

# Convenience functions
def is_billing_enabled() -> bool:
    """Check if billing is enabled"""
    return billing_config.BILLING_ENABLED

def is_beta_phase() -> bool:
    """Check if we're in beta phase"""
    return billing_config.BETA_PHASE

def can_access_feature(plan_name: str, feature_name: str) -> bool:
    """Check if a plan can access a specific feature"""
    return billing_config.can_access_feature(plan_name, feature_name)

def get_feature_limit(plan_name: str, feature_name: str) -> int:
    """Get the limit for a specific feature in a plan"""
    return billing_config.get_feature_limit(plan_name, feature_name)

def get_user_plan(user_id: str = None) -> str:
    """Get the plan for a user"""
    return billing_config.get_user_plan(user_id)

def get_plan_display_info(plan_name: str = None) -> Dict[str, Any]:
    """Get display information for a plan"""
    return billing_config.get_plan_display_info(plan_name)
