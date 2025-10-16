"""
Privacy and Compliance Service
Handles GDPR/CCPA compliance, data anonymization, and ethical AI measures
"""

from typing import Dict, List, Optional, Any
import logging
import json
import hashlib
import re
from datetime import datetime, timedelta
from roleready_api.core.supabase import supabase_client

logger = logging.getLogger(__name__)

class PrivacyComplianceService:
    def __init__(self):
        self.supported_regions = ["US", "EU", "UK", "CA"]  # Supported data residency regions
        self.retention_periods = {
            "resume_data": 365,  # 1 year
            "feedback_data": 90,  # 3 months
            "analytics_data": 730,  # 2 years
            "session_data": 30  # 1 month
        }

    async def anonymize_personal_data(self, text: str, anonymization_level: str = "medium") -> str:
        """
        Anonymize personal information in text based on level
        """
        try:
            if not text:
                return text
            
            # Email addresses
            text = re.sub(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                '[EMAIL]', text
            )
            
            # Phone numbers (various formats)
            text = re.sub(
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                '[PHONE]', text
            )
            
            # Social Security Numbers (US format)
            text = re.sub(
                r'\b\d{3}-\d{2}-\d{4}\b',
                '[SSN]', text
            )
            
            # Credit card numbers
            text = re.sub(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                '[CARD]', text
            )
            
            if anonymization_level == "high":
                # Names (basic heuristic)
                words = text.split()
                anonymized_words = []
                
                for word in words:
                    # Check if word looks like a name (capitalized, alphabetic, 2+ chars)
                    if (len(word) > 2 and word[0].isupper() and word.isalpha() and
                        not word.lower() in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']):
                        anonymized_words.append('[NAME]')
                    else:
                        anonymized_words.append(word)
                
                text = ' '.join(anonymized_words)
            
            # Addresses (basic patterns)
            if anonymization_level in ["medium", "high"]:
                # Street addresses
                text = re.sub(
                    r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b',
                    '[ADDRESS]', text, flags=re.IGNORECASE
                )
                
                # ZIP codes
                text = re.sub(r'\b\d{5}(?:-\d{4})?\b', '[ZIP]', text)
                
                # Cities and states (common patterns)
                text = re.sub(r'\b[A-Za-z\s]+,\s*(?:CA|NY|TX|FL|IL|PA|OH|GA|NC|MI)\b', '[LOCATION]', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return text

    async def hash_personal_identifier(self, identifier: str) -> str:
        """
        Create a hash of personal identifier for pseudonymization
        """
        try:
            # Use SHA-256 with salt for consistent hashing
            salt = "roleready_salt_2024"  # In production, use environment variable
            combined = f"{identifier}{salt}"
            return hashlib.sha256(combined.encode()).hexdigest()[:16]  # First 16 chars
        except Exception as e:
            logger.error(f"Error hashing identifier: {e}")
            return identifier

    async def export_user_data(self, user_id: str) -> Dict:
        """
        Export all user data for GDPR "Right to Data Portability"
        """
        try:
            user_data = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data_retention_policy": self.retention_periods,
                "regions_processed": self.supported_regions
            }
            
            # Get user profile data
            try:
                profile_result = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
                user_data["profile"] = profile_result.data[0] if profile_result.data else None
            except Exception as e:
                logger.warning(f"Could not fetch profile data: {e}")
                user_data["profile"] = None
            
            # Get resume data
            try:
                resumes_result = supabase_client.table("resumes").select("*").eq("user_id", user_id).execute()
                user_data["resumes"] = resumes_result.data or []
            except Exception as e:
                logger.warning(f"Could not fetch resume data: {e}")
                user_data["resumes"] = []
            
            # Get feedback data
            try:
                feedback_result = supabase_client.table("model_feedback").select("*").eq("user_id", user_id).execute()
                user_data["feedback"] = feedback_result.data or []
            except Exception as e:
                logger.warning(f"Could not fetch feedback data: {e}")
                user_data["feedback"] = []
            
            # Get career insights
            try:
                insights_result = supabase_client.table("career_insights").select("*").eq("user_id", user_id).execute()
                user_data["career_insights"] = insights_result.data or []
            except Exception as e:
                logger.warning(f"Could not fetch career insights: {e}")
                user_data["career_insights"] = []
            
            # Get learning paths
            try:
                learning_result = supabase_client.table("learning_paths").select("*").eq("user_id", user_id).execute()
                user_data["learning_paths"] = learning_result.data or []
            except Exception as e:
                logger.warning(f"Could not fetch learning paths: {e}")
                user_data["learning_paths"] = []
            
            # Get team memberships
            try:
                teams_result = supabase_client.table("team_members").select("*").eq("user_id", user_id).execute()
                user_data["team_memberships"] = teams_result.data or []
            except Exception as e:
                logger.warning(f"Could not fetch team memberships: {e}")
                user_data["team_memberships"] = []
            
            return {
                "success": True,
                "user_data": user_data,
                "total_records": len(user_data.get("resumes", [])) + len(user_data.get("feedback", [])) + 
                               len(user_data.get("career_insights", [])) + len(user_data.get("learning_paths", []))
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return {"success": False, "error": str(e)}

    async def delete_user_data(self, user_id: str, delete_type: str = "complete") -> Dict:
        """
        Delete user data for GDPR "Right to be Forgotten"
        """
        try:
            deleted_records = {
                "resumes": 0,
                "feedback": 0,
                "career_insights": 0,
                "learning_paths": 0,
                "team_memberships": 0,
                "profile": 0
            }
            
            # Delete resumes (cascade should handle related data)
            try:
                resumes_result = supabase_client.table("resumes").delete().eq("user_id", user_id).execute()
                deleted_records["resumes"] = len(resumes_result.data) if resumes_result.data else 0
            except Exception as e:
                logger.warning(f"Error deleting resumes: {e}")
            
            # Delete feedback data
            try:
                feedback_result = supabase_client.table("model_feedback").delete().eq("user_id", user_id).execute()
                deleted_records["feedback"] = len(feedback_result.data) if feedback_result.data else 0
            except Exception as e:
                logger.warning(f"Error deleting feedback: {e}")
            
            # Delete career insights
            try:
                insights_result = supabase_client.table("career_insights").delete().eq("user_id", user_id).execute()
                deleted_records["career_insights"] = len(insights_result.data) if insights_result.data else 0
            except Exception as e:
                logger.warning(f"Error deleting career insights: {e}")
            
            # Delete learning paths
            try:
                learning_result = supabase_client.table("learning_paths").delete().eq("user_id", user_id).execute()
                deleted_records["learning_paths"] = len(learning_result.data) if learning_result.data else 0
            except Exception as e:
                logger.warning(f"Error deleting learning paths: {e}")
            
            # Delete team memberships
            try:
                teams_result = supabase_client.table("team_members").delete().eq("user_id", user_id).execute()
                deleted_records["team_memberships"] = len(teams_result.data) if teams_result.data else 0
            except Exception as e:
                logger.warning(f"Error deleting team memberships: {e}")
            
            # Delete profile (if complete deletion)
            if delete_type == "complete":
                try:
                    profile_result = supabase_client.table("profiles").delete().eq("id", user_id).execute()
                    deleted_records["profile"] = len(profile_result.data) if profile_result.data else 0
                except Exception as e:
                    logger.warning(f"Error deleting profile: {e}")
            
            total_deleted = sum(deleted_records.values())
            
            # Log deletion for audit trail
            deletion_log = {
                "user_id": user_id,
                "delete_type": delete_type,
                "deleted_records": deleted_records,
                "total_deleted": total_deleted,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Data deletion completed for user {user_id}: {total_deleted} records")
            
            return {
                "success": True,
                "deleted_records": deleted_records,
                "total_deleted": total_deleted,
                "deletion_log": deletion_log
            }
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return {"success": False, "error": str(e)}

    async def audit_data_processing(self, user_id: str) -> Dict:
        """
        Create audit trail of data processing activities
        """
        try:
            audit_data = {
                "user_id": user_id,
                "audit_date": datetime.utcnow().isoformat(),
                "data_categories": [],
                "processing_purposes": [],
                "retention_periods": self.retention_periods,
                "legal_basis": "Consent and Legitimate Interest"
            }
            
            # Check what data categories exist for user
            data_categories = []
            
            # Resume data
            resumes_result = supabase_client.table("resumes").select("id, created_at, language").eq("user_id", user_id).execute()
            if resumes_result.data:
                data_categories.append({
                    "category": "resume_data",
                    "count": len(resumes_result.data),
                    "purpose": "Resume parsing and analysis",
                    "retention": self.retention_periods["resume_data"]
                })
            
            # Feedback data
            feedback_result = supabase_client.table("model_feedback").select("id, created_at, source").eq("user_id", user_id).execute()
            if feedback_result.data:
                data_categories.append({
                    "category": "feedback_data",
                    "count": len(feedback_result.data),
                    "purpose": "Model improvement and quality assurance",
                    "retention": self.retention_periods["feedback_data"]
                })
            
            # Analytics data (derived from other data)
            if resumes_result.data or feedback_result.data:
                data_categories.append({
                    "category": "analytics_data",
                    "count": "derived",
                    "purpose": "Service improvement and insights",
                    "retention": self.retention_periods["analytics_data"]
                })
            
            audit_data["data_categories"] = data_categories
            
            # Processing purposes
            audit_data["processing_purposes"] = [
                "Resume parsing and analysis",
                "AI-powered resume improvement suggestions",
                "Career guidance and skill gap analysis",
                "Model training and improvement (anonymized)",
                "Service analytics and optimization"
            ]
            
            return {
                "success": True,
                "audit_data": audit_data
            }
            
        except Exception as e:
            logger.error(f"Error creating audit trail: {e}")
            return {"success": False, "error": str(e)}

    async def check_data_retention(self) -> Dict:
        """
        Check and clean up data based on retention policies
        """
        try:
            cleanup_results = {}
            
            for data_type, retention_days in self.retention_periods.items():
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                if data_type == "feedback_data":
                    # Clean up old feedback data
                    try:
                        result = supabase_client.table("model_feedback").delete().lt(
                            "created_at", cutoff_date.isoformat()
                        ).execute()
                        cleanup_results[data_type] = len(result.data) if result.data else 0
                    except Exception as e:
                        logger.warning(f"Error cleaning up {data_type}: {e}")
                        cleanup_results[data_type] = 0
                
                elif data_type == "resume_data":
                    # Clean up old resumes (be more conservative)
                    try:
                        # Only clean up resumes older than 2 years
                        old_cutoff = datetime.utcnow() - timedelta(days=730)
                        result = supabase_client.table("resumes").delete().lt(
                            "created_at", old_cutoff.isoformat()
                        ).execute()
                        cleanup_results[data_type] = len(result.data) if result.data else 0
                    except Exception as e:
                        logger.warning(f"Error cleaning up {data_type}: {e}")
                        cleanup_results[data_type] = 0
            
            total_cleaned = sum(cleanup_results.values())
            
            logger.info(f"Data retention cleanup completed: {total_cleaned} records cleaned")
            
            return {
                "success": True,
                "cleanup_results": cleanup_results,
                "total_cleaned": total_cleaned,
                "cleanup_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in data retention cleanup: {e}")
            return {"success": False, "error": str(e)}

    async def generate_privacy_report(self) -> Dict:
        """
        Generate privacy and compliance report
        """
        try:
            report = {
                "report_date": datetime.utcnow().isoformat(),
                "data_residency_regions": self.supported_regions,
                "retention_policies": self.retention_periods,
                "anonymization_levels": ["low", "medium", "high"],
                "compliance_frameworks": ["GDPR", "CCPA", "SOC 2"],
                "data_processing_activities": [
                    "Resume parsing and analysis",
                    "AI-powered content generation",
                    "Career guidance and recommendations",
                    "Model training and improvement",
                    "Analytics and insights"
                ],
                "user_rights": [
                    "Right to access personal data",
                    "Right to rectification",
                    "Right to erasure (right to be forgotten)",
                    "Right to data portability",
                    "Right to object to processing",
                    "Right to withdraw consent"
                ],
                "security_measures": [
                    "Data encryption at rest and in transit",
                    "Access controls and authentication",
                    "Regular security audits",
                    "Data anonymization for training",
                    "Secure data deletion"
                ]
            }
            
            # Get current statistics
            try:
                # Count total users
                users_result = supabase_client.table("profiles").select("id", count="exact").execute()
                report["total_users"] = users_result.count
                
                # Count total resumes
                resumes_result = supabase_client.table("resumes").select("id", count="exact").execute()
                report["total_resumes"] = resumes_result.count
                
                # Count total feedback
                feedback_result = supabase_client.table("model_feedback").select("id", count="exact").execute()
                report["total_feedback"] = feedback_result.count
                
            except Exception as e:
                logger.warning(f"Could not fetch statistics: {e}")
                report["statistics"] = "Unable to fetch current statistics"
            
            return {
                "success": True,
                "privacy_report": report
            }
            
        except Exception as e:
            logger.error(f"Error generating privacy report: {e}")
            return {"success": False, "error": str(e)}

# Global instance
privacy_compliance_service = PrivacyComplianceService()
