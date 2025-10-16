"""
Feedback collection and continuous learning system
Collects user feedback on AI suggestions to improve model performance
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy import text
from roleready_api.core.supabase import supabase_client

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.model_version = "1.0.0"  # Current model version
        self.feedback_batch_size = 100

    async def collect_feedback(
        self,
        user_id: str,
        resume_id: str,
        source: str,
        suggestion: str,
        final: str,
        accepted: bool,
        confidence_score: Optional[float] = None
    ) -> Dict:
        """
        Collect feedback on AI suggestions
        """
        try:
            feedback_data = {
                "user_id": user_id,
                "resume_id": resume_id,
                "source": source,
                "suggestion": suggestion,
                "final": final,
                "accepted": accepted,
                "confidence_score": confidence_score,
                "model_version": self.model_version,
                "created_at": datetime.utcnow().isoformat()
            }

            result = supabase_client.table("model_feedback").insert(feedback_data).execute()
            
            if result.data:
                logger.info(f"Feedback collected for user {user_id}, source: {source}")
                return {"success": True, "feedback_id": result.data[0]["id"]}
            else:
                logger.error(f"Failed to collect feedback: {result}")
                return {"success": False, "error": "Database insertion failed"}
                
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return {"success": False, "error": str(e)}

    async def get_feedback_stats(self, user_id: str) -> Dict:
        """
        Get feedback statistics for a user
        """
        try:
            # Get overall acceptance rate
            result = supabase_client.table("model_feedback").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                return {
                    "total_feedback": 0,
                    "acceptance_rate": 0.0,
                    "sources": {},
                    "confidence_scores": {"avg": 0.0, "min": 0.0, "max": 0.0}
                }

            feedback_items = result.data
            total = len(feedback_items)
            accepted = sum(1 for item in feedback_items if item["accepted"])
            acceptance_rate = accepted / total if total > 0 else 0.0

            # Group by source
            sources = {}
            for item in feedback_items:
                source = item["source"]
                if source not in sources:
                    sources[source] = {"total": 0, "accepted": 0}
                sources[source]["total"] += 1
                if item["accepted"]:
                    sources[source]["accepted"] += 1

            # Calculate source acceptance rates
            for source in sources:
                sources[source]["acceptance_rate"] = (
                    sources[source]["accepted"] / sources[source]["total"] 
                    if sources[source]["total"] > 0 else 0.0
                )

            # Confidence score statistics
            confidence_scores = [item["confidence_score"] for item in feedback_items if item["confidence_score"]]
            confidence_stats = {
                "avg": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "min": min(confidence_scores) if confidence_scores else 0.0,
                "max": max(confidence_scores) if confidence_scores else 0.0
            }

            return {
                "total_feedback": total,
                "acceptance_rate": acceptance_rate,
                "sources": sources,
                "confidence_scores": confidence_stats,
                "model_version": self.model_version
            }

        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {"error": str(e)}

    async def export_feedback_for_training(self, days_back: int = 30) -> List[Dict]:
        """
        Export anonymized feedback data for model training
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = supabase_client.table("model_feedback").select(
                "source, suggestion, final, accepted, confidence_score, model_version, created_at"
            ).gte("created_at", cutoff_date.isoformat()).execute()

            if not result.data:
                return []

            # Anonymize the data
            anonymized_data = []
            for item in result.data:
                anonymized_item = {
                    "source": item["source"],
                    "suggestion": self._anonymize_text(item["suggestion"]),
                    "final": self._anonymize_text(item["final"]),
                    "accepted": item["accepted"],
                    "confidence_score": item["confidence_score"],
                    "model_version": item["model_version"],
                    "created_at": item["created_at"]
                }
                anonymized_data.append(anonymized_item)

            logger.info(f"Exported {len(anonymized_data)} feedback items for training")
            return anonymized_data

        except Exception as e:
            logger.error(f"Error exporting feedback: {e}")
            return []

    def _anonymize_text(self, text: str) -> str:
        """
        Anonymize personal information in text
        """
        import re
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Remove names (basic heuristic - words that start with capital letters)
        # This is a simple approach; in production, you'd want more sophisticated NER
        words = text.split()
        anonymized_words = []
        for word in words:
            if len(word) > 2 and word[0].isupper() and word.isalpha():
                anonymized_words.append('[NAME]')
            else:
                anonymized_words.append(word)
        
        return ' '.join(anonymized_words)

    async def get_model_performance_metrics(self) -> Dict:
        """
        Get overall model performance metrics
        """
        try:
            # Get recent feedback (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            result = supabase_client.table("model_feedback").select("*").gte(
                "created_at", cutoff_date.isoformat()
            ).execute()

            if not result.data:
                return {
                    "total_feedback": 0,
                    "acceptance_rate": 0.0,
                    "sources": {},
                    "confidence_correlation": 0.0
                }

            feedback_items = result.data
            total = len(feedback_items)
            accepted = sum(1 for item in feedback_items if item["accepted"])
            acceptance_rate = accepted / total if total > 0 else 0.0

            # Group by source
            sources = {}
            for item in feedback_items:
                source = item["source"]
                if source not in sources:
                    sources[source] = {"total": 0, "accepted": 0}
                sources[source]["total"] += 1
                if item["accepted"]:
                    sources[source]["accepted"] += 1

            # Calculate source acceptance rates
            for source in sources:
                sources[source]["acceptance_rate"] = (
                    sources[source]["accepted"] / sources[source]["total"] 
                    if sources[source]["total"] > 0 else 0.0
                )

            # Calculate confidence correlation
            confidence_items = [(item["confidence_score"], item["accepted"]) 
                              for item in feedback_items if item["confidence_score"] is not None]
            
            if confidence_items:
                high_conf_acceptance = sum(1 for conf, acc in confidence_items if conf > 0.8 and acc) / max(
                    sum(1 for conf, acc in confidence_items if conf > 0.8), 1
                )
                low_conf_acceptance = sum(1 for conf, acc in confidence_items if conf < 0.5 and acc) / max(
                    sum(1 for conf, acc in confidence_items if conf < 0.5), 1
                )
                confidence_correlation = high_conf_acceptance - low_conf_acceptance
            else:
                confidence_correlation = 0.0

            return {
                "total_feedback": total,
                "acceptance_rate": acceptance_rate,
                "sources": sources,
                "confidence_correlation": confidence_correlation,
                "model_version": self.model_version,
                "period_days": 30
            }

        except Exception as e:
            logger.error(f"Error getting model performance metrics: {e}")
            return {"error": str(e)}

    async def cleanup_old_feedback(self, days_to_keep: int = 90) -> int:
        """
        Clean up old feedback data to maintain database performance
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = supabase_client.table("model_feedback").delete().lt(
                "created_at", cutoff_date.isoformat()
            ).execute()

            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {deleted_count} old feedback records")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old feedback: {e}")
            return 0

# Global instance
feedback_service = FeedbackService()