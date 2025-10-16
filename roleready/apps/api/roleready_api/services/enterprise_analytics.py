"""
Enterprise Analytics and Usage Metering for RoleReady
Provides org-level analytics, usage tracking, and business intelligence
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class UsageMetrics:
    """Usage metrics for an organization"""
    org_id: str
    period_start: datetime
    period_end: datetime
    total_users: int
    active_users: int
    total_resumes_processed: int
    total_api_calls: int
    total_storage_used_mb: float
    feature_usage: Dict[str, int]
    user_engagement_score: float
    cost_metrics: Dict[str, float]

@dataclass
class BusinessMetrics:
    """Business intelligence metrics"""
    org_id: str
    period_start: datetime
    period_end: datetime
    revenue: float
    cost_per_user: float
    user_retention_rate: float
    feature_adoption_rate: Dict[str, float]
    satisfaction_score: float
    support_tickets: int
    churn_rate: float

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    org_id: str
    period_start: datetime
    period_end: datetime
    avg_response_time_ms: float
    uptime_percentage: float
    error_rate: float
    throughput_requests_per_second: float
    resource_utilization: Dict[str, float]
    sla_compliance: float

@dataclass
class SecurityMetrics:
    """Security and compliance metrics"""
    org_id: str
    period_start: datetime
    period_end: datetime
    failed_login_attempts: int
    suspicious_activities: int
    data_breaches: int
    compliance_violations: int
    security_incidents: int
    audit_logs_count: int

class UsageTracker:
    """Tracks usage metrics for organizations"""
    
    def __init__(self):
        self.usage_data = defaultdict(list)
        self.feature_registry = {
            'resume_parsing': 'Resume Parsing',
            'job_matching': 'Job Matching',
            'resume_rewriting': 'Resume Rewriting',
            'career_advisor': 'Career Advisor',
            'team_collaboration': 'Team Collaboration',
            'api_access': 'API Access',
            'multilingual': 'Multilingual Support',
            'export_docx': 'Document Export',
            'feedback_system': 'Feedback System',
            'analytics': 'Analytics Dashboard'
        }
    
    def record_usage(
        self,
        org_id: str,
        user_id: str,
        feature: str,
        metadata: Dict = None
    ):
        """Record usage of a feature"""
        
        usage_record = {
            'timestamp': datetime.now().isoformat(),
            'org_id': org_id,
            'user_id': user_id,
            'feature': feature,
            'metadata': metadata or {}
        }
        
        self.usage_data[org_id].append(usage_record)
        
        # Keep only last 90 days of data
        cutoff_date = datetime.now() - timedelta(days=90)
        self.usage_data[org_id] = [
            record for record in self.usage_data[org_id]
            if datetime.fromisoformat(record['timestamp']) > cutoff_date
        ]
    
    def get_usage_metrics(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> UsageMetrics:
        """Get usage metrics for an organization"""
        
        org_usage = self.usage_data.get(org_id, [])
        
        # Filter by period
        period_usage = [
            record for record in org_usage
            if period_start <= datetime.fromisoformat(record['timestamp']) <= period_end
        ]
        
        # Calculate metrics
        unique_users = set(record['user_id'] for record in period_usage)
        total_users = len(unique_users)
        
        # Active users (used any feature in last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        active_users = len(set(
            record['user_id'] for record in period_usage
            if datetime.fromisoformat(record['timestamp']) > recent_cutoff
        ))
        
        # Feature usage counts
        feature_usage = defaultdict(int)
        for record in period_usage:
            feature_usage[record['feature']] += 1
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(period_usage, total_users)
        
        # Calculate cost metrics
        cost_metrics = self._calculate_cost_metrics(period_usage, total_users)
        
        return UsageMetrics(
            org_id=org_id,
            period_start=period_start,
            period_end=period_end,
            total_users=total_users,
            active_users=active_users,
            total_resumes_processed=feature_usage.get('resume_parsing', 0),
            total_api_calls=feature_usage.get('api_access', 0),
            total_storage_used_mb=self._estimate_storage_usage(period_usage),
            feature_usage=dict(feature_usage),
            user_engagement_score=engagement_score,
            cost_metrics=cost_metrics
        )
    
    def _calculate_engagement_score(self, usage_records: List[Dict], total_users: int) -> float:
        """Calculate user engagement score"""
        
        if total_users == 0:
            return 0.0
        
        # Calculate average features used per user
        user_features = defaultdict(set)
        for record in usage_records:
            user_features[record['user_id']].add(record['feature'])
        
        avg_features_per_user = sum(len(features) for features in user_features.values()) / total_users
        
        # Calculate frequency of usage
        total_usage = len(usage_records)
        avg_usage_per_user = total_usage / total_users
        
        # Normalize to 0-1 scale
        engagement_score = min(1.0, (avg_features_per_user / 5.0) * 0.6 + (avg_usage_per_user / 20.0) * 0.4)
        
        return engagement_score
    
    def _calculate_cost_metrics(self, usage_records: List[Dict], total_users: int) -> Dict[str, float]:
        """Calculate cost-related metrics"""
        
        # Cost per feature (mock pricing)
        feature_costs = {
            'resume_parsing': 0.10,
            'job_matching': 0.05,
            'resume_rewriting': 0.15,
            'career_advisor': 0.20,
            'api_access': 0.01,
            'multilingual': 0.05,
            'export_docx': 0.02
        }
        
        total_cost = 0.0
        feature_costs_incurred = defaultdict(float)
        
        for record in usage_records:
            feature = record['feature']
            cost = feature_costs.get(feature, 0.0)
            total_cost += cost
            feature_costs_incurred[feature] += cost
        
        return {
            'total_cost': total_cost,
            'cost_per_user': total_cost / max(total_users, 1),
            'feature_costs': dict(feature_costs_incurred),
            'monthly_estimate': total_cost * 30  # Assuming daily usage pattern
        }
    
    def _estimate_storage_usage(self, usage_records: List[Dict]) -> float:
        """Estimate storage usage in MB"""
        
        # Estimate storage based on usage patterns
        storage_estimates = {
            'resume_parsing': 0.5,  # MB per resume
            'export_docx': 0.1,     # MB per export
            'team_collaboration': 0.2,  # MB per collaboration
            'feedback_system': 0.05  # MB per feedback
        }
        
        total_storage = 0.0
        for record in usage_records:
            feature = record['feature']
            storage_per_use = storage_estimates.get(feature, 0.0)
            total_storage += storage_per_use
        
        return total_storage

class BusinessIntelligence:
    """Provides business intelligence and analytics"""
    
    def __init__(self):
        self.revenue_tracker = RevenueTracker()
        self.customer_success = CustomerSuccessTracker()
    
    def calculate_business_metrics(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> BusinessMetrics:
        """Calculate business metrics for an organization"""
        
        # Get revenue data
        revenue_data = self.revenue_tracker.get_revenue_for_period(org_id, period_start, period_end)
        
        # Get customer success metrics
        success_metrics = self.customer_success.get_success_metrics(org_id, period_start, period_end)
        
        # Calculate derived metrics
        user_retention_rate = self._calculate_retention_rate(org_id, period_start, period_end)
        feature_adoption_rate = self._calculate_feature_adoption_rate(org_id, period_start, period_end)
        
        return BusinessMetrics(
            org_id=org_id,
            period_start=period_start,
            period_end=period_end,
            revenue=revenue_data['total_revenue'],
            cost_per_user=revenue_data['cost_per_user'],
            user_retention_rate=user_retention_rate,
            feature_adoption_rate=feature_adoption_rate,
            satisfaction_score=success_metrics['satisfaction_score'],
            support_tickets=success_metrics['support_tickets'],
            churn_rate=success_metrics['churn_rate']
        )
    
    def _calculate_retention_rate(self, org_id: str, period_start: datetime, period_end: datetime) -> float:
        """Calculate user retention rate"""
        
        # Mock calculation (in production, use actual user activity data)
        base_retention = 0.85
        
        # Adjust based on engagement (mock)
        engagement_factor = np.random.uniform(0.8, 1.2)
        
        return min(1.0, base_retention * engagement_factor)
    
    def _calculate_feature_adoption_rate(self, org_id: str, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate feature adoption rates"""
        
        # Mock feature adoption rates
        features = [
            'resume_parsing', 'job_matching', 'resume_rewriting',
            'career_advisor', 'team_collaboration', 'api_access',
            'multilingual', 'export_docx', 'feedback_system'
        ]
        
        adoption_rates = {}
        for feature in features:
            # Simulate realistic adoption rates
            base_rate = np.random.uniform(0.3, 0.9)
            adoption_rates[feature] = base_rate
        
        return adoption_rates

class RevenueTracker:
    """Tracks revenue and pricing metrics"""
    
    def __init__(self):
        self.pricing_tiers = {
            'starter': {'price': 29.99, 'users': 5},
            'professional': {'price': 99.99, 'users': 25},
            'enterprise': {'price': 299.99, 'users': 100},
            'custom': {'price': 0.0, 'users': 0}  # Custom pricing
        }
    
    def get_revenue_for_period(self, org_id: str, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Get revenue data for a period"""
        
        # Mock revenue calculation
        base_revenue = np.random.uniform(1000, 10000)
        
        # Adjust for period length
        period_days = (period_end - period_start).days
        monthly_revenue = base_revenue * (30 / max(period_days, 1))
        
        # Estimate users and cost per user
        estimated_users = np.random.randint(10, 100)
        cost_per_user = monthly_revenue / max(estimated_users, 1)
        
        return {
            'total_revenue': monthly_revenue,
            'cost_per_user': cost_per_user,
            'estimated_users': estimated_users,
            'revenue_growth': np.random.uniform(0.05, 0.25)
        }

class CustomerSuccessTracker:
    """Tracks customer success metrics"""
    
    def __init__(self):
        self.support_data = defaultdict(list)
        self.satisfaction_data = defaultdict(list)
    
    def get_success_metrics(self, org_id: str, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Get customer success metrics"""
        
        # Mock satisfaction score
        satisfaction_score = np.random.uniform(3.5, 4.8)
        
        # Mock support tickets
        support_tickets = np.random.randint(0, 20)
        
        # Mock churn rate
        churn_rate = np.random.uniform(0.02, 0.15)
        
        return {
            'satisfaction_score': satisfaction_score,
            'support_tickets': support_tickets,
            'churn_rate': churn_rate,
            'net_promoter_score': np.random.uniform(6.0, 9.5),
            'time_to_value_days': np.random.randint(7, 30)
        }

class PerformanceMonitor:
    """Monitors system performance metrics"""
    
    def __init__(self):
        self.performance_data = defaultdict(list)
    
    def get_performance_metrics(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> PerformanceMetrics:
        """Get performance metrics for an organization"""
        
        # Mock performance data
        avg_response_time = np.random.uniform(100, 500)  # ms
        uptime_percentage = np.random.uniform(99.5, 99.9)
        error_rate = np.random.uniform(0.001, 0.01)
        throughput = np.random.uniform(100, 1000)  # requests per second
        
        resource_utilization = {
            'cpu_percent': np.random.uniform(20, 80),
            'memory_percent': np.random.uniform(30, 70),
            'disk_percent': np.random.uniform(10, 60),
            'network_mbps': np.random.uniform(50, 200)
        }
        
        sla_compliance = np.random.uniform(0.95, 1.0)
        
        return PerformanceMetrics(
            org_id=org_id,
            period_start=period_start,
            period_end=period_end,
            avg_response_time_ms=avg_response_time,
            uptime_percentage=uptime_percentage,
            error_rate=error_rate,
            throughput_requests_per_second=throughput,
            resource_utilization=resource_utilization,
            sla_compliance=sla_compliance
        )

class SecurityMonitor:
    """Monitors security and compliance metrics"""
    
    def __init__(self):
        self.security_events = defaultdict(list)
    
    def get_security_metrics(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> SecurityMetrics:
        """Get security metrics for an organization"""
        
        # Mock security data
        failed_logins = np.random.randint(0, 50)
        suspicious_activities = np.random.randint(0, 5)
        data_breaches = np.random.randint(0, 1)  # Hopefully 0!
        compliance_violations = np.random.randint(0, 3)
        security_incidents = np.random.randint(0, 2)
        audit_logs = np.random.randint(1000, 10000)
        
        return SecurityMetrics(
            org_id=org_id,
            period_start=period_start,
            period_end=period_end,
            failed_login_attempts=failed_logins,
            suspicious_activities=suspicious_activities,
            data_breaches=data_breaches,
            compliance_violations=compliance_violations,
            security_incidents=security_incidents,
            audit_logs_count=audit_logs
        )

class EnterpriseDashboard:
    """Main enterprise dashboard aggregator"""
    
    def __init__(self):
        self.usage_tracker = UsageTracker()
        self.business_intelligence = BusinessIntelligence()
        self.performance_monitor = PerformanceMonitor()
        self.security_monitor = SecurityMonitor()
    
    def get_comprehensive_dashboard(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict:
        """Get comprehensive dashboard data"""
        
        # Gather all metrics
        usage_metrics = self.usage_tracker.get_usage_metrics(org_id, period_start, period_end)
        business_metrics = self.business_intelligence.calculate_business_metrics(org_id, period_start, period_end)
        performance_metrics = self.performance_monitor.get_performance_metrics(org_id, period_start, period_end)
        security_metrics = self.security_monitor.get_security_metrics(org_id, period_start, period_end)
        
        # Calculate key performance indicators
        kpis = self._calculate_kpis(usage_metrics, business_metrics, performance_metrics)
        
        # Generate insights and recommendations
        insights = self._generate_insights(usage_metrics, business_metrics, performance_metrics, security_metrics)
        recommendations = self._generate_recommendations(usage_metrics, business_metrics, performance_metrics)
        
        # Create dashboard data structure
        dashboard_data = {
            'organization_id': org_id,
            'period': {
                'start': period_start.isoformat(),
                'end': period_end.isoformat()
            },
            'kpis': kpis,
            'usage_metrics': asdict(usage_metrics),
            'business_metrics': asdict(business_metrics),
            'performance_metrics': asdict(performance_metrics),
            'security_metrics': asdict(security_metrics),
            'insights': insights,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard_data
    
    def _calculate_kpis(self, usage: UsageMetrics, business: BusinessMetrics, performance: PerformanceMetrics) -> Dict:
        """Calculate key performance indicators"""
        
        return {
            'user_engagement': usage.user_engagement_score,
            'revenue_per_user': business.cost_per_user,
            'system_uptime': performance.uptime_percentage,
            'user_retention': business.user_retention_rate,
            'feature_adoption': np.mean(list(business.feature_adoption_rate.values())),
            'cost_efficiency': usage.cost_metrics['cost_per_user'],
            'satisfaction_score': business.satisfaction_score,
            'sla_compliance': performance.sla_compliance
        }
    
    def _generate_insights(self, usage: UsageMetrics, business: BusinessMetrics, performance: PerformanceMetrics, security: SecurityMetrics) -> List[str]:
        """Generate insights from metrics"""
        
        insights = []
        
        # Usage insights
        if usage.user_engagement_score > 0.8:
            insights.append("High user engagement indicates strong product-market fit")
        elif usage.user_engagement_score < 0.4:
            insights.append("Low user engagement - consider user onboarding improvements")
        
        # Business insights
        if business.churn_rate > 0.1:
            insights.append("High churn rate detected - investigate customer satisfaction issues")
        
        if business.satisfaction_score > 4.5:
            insights.append("Excellent customer satisfaction scores")
        
        # Performance insights
        if performance.avg_response_time_ms > 500:
            insights.append("Response times are high - consider performance optimization")
        
        if performance.uptime_percentage < 99.5:
            insights.append("Uptime below SLA target - investigate infrastructure issues")
        
        # Security insights
        if security.security_incidents > 0:
            insights.append("Security incidents detected - review security protocols")
        
        if security.failed_login_attempts > 100:
            insights.append("High number of failed login attempts - consider additional security measures")
        
        return insights
    
    def _generate_recommendations(self, usage: UsageMetrics, business: BusinessMetrics, performance: PerformanceMetrics) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Usage recommendations
        if usage.active_users / max(usage.total_users, 1) < 0.7:
            recommendations.append("Improve user activation - consider in-app tutorials and onboarding")
        
        # Feature usage recommendations
        underused_features = [
            feature for feature, count in usage.feature_usage.items()
            if count < 10 and feature in ['career_advisor', 'multilingual', 'team_collaboration']
        ]
        
        if underused_features:
            recommendations.append(f"Promote underused features: {', '.join(underused_features)}")
        
        # Business recommendations
        if business.cost_per_user > 50:
            recommendations.append("High cost per user - consider pricing optimization or feature bundling")
        
        if business.support_tickets > 50:
            recommendations.append("High support ticket volume - consider improving documentation and self-service options")
        
        # Performance recommendations
        if performance.error_rate > 0.01:
            recommendations.append("Error rate above threshold - investigate and fix critical issues")
        
        if performance.avg_response_time_ms > 300:
            recommendations.append("Optimize API response times - consider caching and database optimization")
        
        return recommendations
    
    def get_usage_trends(self, org_id: str, days: int = 30) -> Dict:
        """Get usage trends over time"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Mock trend data
        dates = [(start_date + timedelta(days=i)).isoformat() for i in range(days)]
        
        trends = {
            'daily_active_users': [np.random.randint(10, 50) for _ in range(days)],
            'daily_api_calls': [np.random.randint(100, 1000) for _ in range(days)],
            'daily_resumes_processed': [np.random.randint(20, 200) for _ in range(days)],
            'daily_revenue': [np.random.uniform(50, 500) for _ in range(days)],
            'dates': dates
        }
        
        return trends
    
    def export_dashboard_data(self, org_id: str, period_start: datetime, period_end: datetime, format: str = 'json') -> str:
        """Export dashboard data in specified format"""
        
        dashboard_data = self.get_comprehensive_dashboard(org_id, period_start, period_end)
        
        if format.lower() == 'json':
            return json.dumps(dashboard_data, indent=2)
        elif format.lower() == 'csv':
            # Convert to CSV format (simplified)
            csv_data = self._convert_to_csv(dashboard_data)
            return csv_data
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _convert_to_csv(self, dashboard_data: Dict) -> str:
        """Convert dashboard data to CSV format"""
        
        # Simplified CSV conversion
        csv_lines = []
        
        # KPI data
        csv_lines.append("Metric,Value")
        for metric, value in dashboard_data['kpis'].items():
            csv_lines.append(f"{metric},{value}")
        
        return '\n'.join(csv_lines)

# Global enterprise dashboard instance
enterprise_dashboard = EnterpriseDashboard()

# Convenience functions
def get_enterprise_dashboard(org_id: str, period_start: datetime, period_end: datetime) -> Dict:
    """Get comprehensive enterprise dashboard"""
    return enterprise_dashboard.get_comprehensive_dashboard(org_id, period_start, period_end)

def record_enterprise_usage(org_id: str, user_id: str, feature: str, metadata: Dict = None):
    """Record enterprise usage"""
    enterprise_dashboard.usage_tracker.record_usage(org_id, user_id, feature, metadata)

def get_usage_trends(org_id: str, days: int = 30) -> Dict:
    """Get usage trends for organization"""
    return enterprise_dashboard.get_usage_trends(org_id, days)

def export_dashboard_data(org_id: str, period_start: datetime, period_end: datetime, format: str = 'json') -> str:
    """Export dashboard data"""
    return enterprise_dashboard.export_dashboard_data(org_id, period_start, period_end, format)
