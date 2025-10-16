"""
Continuous Learning Service
Handles model training pipeline, feedback analysis, and model improvement
"""

from typing import Dict, List, Optional, Tuple
import logging
import json
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from roleready_api.core.supabase import supabase_client
from roleready_api.core.redis_client import redis_client, get_feedback_stats_key
from .feedback import feedback_service

logger = logging.getLogger(__name__)

class ContinuousLearningService:
    def __init__(self):
        self.model_version = "1.0.0"
        self.training_batch_size = 1000
        self.min_feedback_samples = 100
        self.improvement_threshold = 0.05  # 5% improvement required to promote model

    async def collect_training_data(self, days_back: int = 30) -> Dict:
        """
        Collect and prepare training data from feedback
        """
        try:
            # Get feedback data
            feedback_data = await feedback_service.export_feedback_for_training(days_back)
            
            if len(feedback_data) < self.min_feedback_samples:
                return {
                    "success": False,
                    "message": f"Insufficient training data: {len(feedback_data)} samples (minimum: {self.min_feedback_samples})",
                    "sample_count": len(feedback_data)
                }
            
            # Prepare training dataset
            training_data = []
            for item in feedback_data:
                training_sample = {
                    "input": item["suggestion"],
                    "output": item["final"],
                    "label": 1 if item["accepted"] else 0,
                    "confidence": item.get("confidence_score", 0.5),
                    "source": item["source"],
                    "model_version": item["model_version"]
                }
                training_data.append(training_sample)
            
            # Split into train/validation/test
            train_data, temp_data = train_test_split(
                training_data, test_size=0.3, random_state=42, stratify=[d["label"] for d in training_data]
            )
            val_data, test_data = train_test_split(
                temp_data, test_size=0.5, random_state=42, stratify=[d["label"] for d in temp_data]
            )
            
            return {
                "success": True,
                "sample_count": len(training_data),
                "train_count": len(train_data),
                "val_count": len(val_data),
                "test_count": len(test_data),
                "training_data": train_data,
                "validation_data": val_data,
                "test_data": test_data
            }
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_model_performance(self, test_data: List[Dict]) -> Dict:
        """
        Analyze current model performance on test data
        """
        try:
            if not test_data:
                return {"error": "No test data provided"}
            
            # Simulate model predictions (in production, this would use actual model)
            predictions = []
            true_labels = []
            
            for item in test_data:
                # Simple heuristic based on confidence and text similarity
                confidence = item.get("confidence", 0.5)
                input_text = item["input"].lower()
                output_text = item["output"].lower()
                
                # Calculate text similarity
                similarity = self._calculate_text_similarity(input_text, output_text)
                
                # Simple prediction logic (in production, use trained model)
                predicted_score = (confidence * 0.6) + (similarity * 0.4)
                prediction = 1 if predicted_score > 0.6 else 0
                
                predictions.append(prediction)
                true_labels.append(item["label"])
            
            # Calculate metrics
            accuracy = accuracy_score(true_labels, predictions)
            precision = precision_score(true_labels, predictions, zero_division=0)
            recall = recall_score(true_labels, predictions, zero_division=0)
            f1 = f1_score(true_labels, predictions, zero_division=0)
            
            # Calculate confidence calibration
            confidence_scores = [item.get("confidence", 0.5) for item in test_data]
            high_conf_accuracy = self._calculate_high_confidence_accuracy(
                predictions, true_labels, confidence_scores
            )
        
        return {
                "accuracy": round(accuracy, 3),
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3),
                "high_confidence_accuracy": round(high_conf_accuracy, 3),
                "sample_count": len(test_data),
                "positive_samples": sum(true_labels),
                "negative_samples": len(true_labels) - sum(true_labels)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing model performance: {e}")
            return {"error": str(e)}

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (in production, use more sophisticated methods)
        """
        try:
            # Simple word overlap similarity
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 or not words2:
            return 0.0
        
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
        
    def _calculate_high_confidence_accuracy(
        self, predictions: List[int], true_labels: List[int], confidence_scores: List[float]
    ) -> float:
        """
        Calculate accuracy for high-confidence predictions
        """
        try:
            high_conf_threshold = 0.8
            high_conf_indices = [
                i for i, conf in enumerate(confidence_scores) if conf >= high_conf_threshold
            ]
            
            if not high_conf_indices:
                return 0.0
            
            high_conf_predictions = [predictions[i] for i in high_conf_indices]
            high_conf_labels = [true_labels[i] for i in high_conf_indices]
            
            correct = sum(1 for p, l in zip(high_conf_predictions, high_conf_labels) if p == l)
            return correct / len(high_conf_indices)
            
        except Exception as e:
            logger.error(f"Error calculating high confidence accuracy: {e}")
            return 0.0

    async def train_model(self, training_data: List[Dict], validation_data: List[Dict]) -> Dict:
        """
        Train a new model version (simplified version - in production, use actual ML training)
        """
        try:
            # In production, this would involve:
            # 1. Fine-tuning a pre-trained model (e.g., BERT, GPT)
            # 2. Using techniques like LoRA for efficient fine-tuning
            # 3. Hyperparameter optimization
            # 4. Model validation and selection
            
            # For now, simulate training process
            logger.info(f"Training model with {len(training_data)} training samples")
            
            # Simulate training metrics
            training_metrics = {
                "loss": 0.25,
                "accuracy": 0.78,
                "epochs": 5,
                "training_time_minutes": 15
            }
            
            # Validate on validation set
            val_metrics = await self.analyze_model_performance(validation_data)
            
            if "error" in val_metrics:
                return {"success": False, "error": val_metrics["error"]}
            
            # Create new model version
            new_version = self._generate_new_version()
            
            return {
                "success": True,
                "new_version": new_version,
                "training_metrics": training_metrics,
                "validation_metrics": val_metrics,
                "model_ready": val_metrics.get("accuracy", 0) > 0.7
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"success": False, "error": str(e)}

    def _generate_new_version(self) -> str:
        """
        Generate a new model version string
        """
        # Simple versioning scheme
        version_parts = self.model_version.split(".")
        major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
        
        # Increment patch version
        patch += 1
        if patch > 9:
            patch = 0
            minor += 1
            if minor > 9:
                minor = 0
                major += 1
        
        return f"{major}.{minor}.{patch}"

    async def evaluate_model_candidates(
        self,
        current_model_version: str, 
        candidate_versions: List[str]
    ) -> Dict:
        """
        Evaluate multiple model candidates and select the best one
        """
        try:
            # Get test data for evaluation
            test_data_result = await self.collect_training_data(days_back=7)
            
            if not test_data_result["success"]:
                return {"success": False, "error": "Failed to collect test data"}
            
            test_data = test_data_result["test_data"]
            
            # Evaluate current model
            current_metrics = await self.analyze_model_performance(test_data)
            
            # Evaluate candidate models (simplified)
            best_candidate = None
            best_score = 0
            
            for version in candidate_versions:
                # Simulate evaluation (in production, load and test actual models)
                candidate_metrics = await self._simulate_model_evaluation(version, test_data)
                
                # Use F1 score as primary metric
                f1_score = candidate_metrics.get("f1_score", 0)
                
                if f1_score > best_score:
                    best_score = f1_score
                    best_candidate = {
                        "version": version,
                        "metrics": candidate_metrics
                    }
            
            # Check if best candidate is significantly better
            current_f1 = current_metrics.get("f1_score", 0)
            improvement = best_score - current_f1
            
            should_promote = (
                best_candidate is not None and 
                improvement >= self.improvement_threshold
            )
            
            return {
                "success": True,
                "current_metrics": current_metrics,
                "best_candidate": best_candidate,
                "improvement": improvement,
                "should_promote": should_promote,
                "promotion_threshold": self.improvement_threshold
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model candidates: {e}")
            return {"success": False, "error": str(e)}

    async def _simulate_model_evaluation(self, version: str, test_data: List[Dict]) -> Dict:
        """
        Simulate model evaluation (in production, this would test actual trained models)
        """
        # Simulate different performance based on version
        base_metrics = await self.analyze_model_performance(test_data)
        
        # Add some variation based on version
        version_factor = hash(version) % 100 / 1000  # Small random variation
        
        return {
            "accuracy": round(base_metrics["accuracy"] + version_factor, 3),
            "precision": round(base_metrics["precision"] + version_factor * 0.8, 3),
            "recall": round(base_metrics["recall"] + version_factor * 1.2, 3),
            "f1_score": round(base_metrics["f1_score"] + version_factor, 3),
            "high_confidence_accuracy": round(base_metrics["high_confidence_accuracy"] + version_factor * 0.5, 3)
        }

    async def deploy_model(self, version: str, deployment_strategy: str = "canary") -> Dict:
        """
        Deploy a new model version
        """
        try:
            if deployment_strategy == "canary":
                # Deploy to 5% of traffic first
                traffic_percentage = 5
                deployment_phase = "canary"
            elif deployment_strategy == "staging":
                # Deploy to staging environment
                traffic_percentage = 0
                deployment_phase = "staging"
            else:
                # Full deployment
                traffic_percentage = 100
                deployment_phase = "full"
            
            # Update model version in database
            deployment_record = {
                "version": version,
                "deployment_strategy": deployment_strategy,
                "traffic_percentage": traffic_percentage,
                "deployment_phase": deployment_phase,
                "deployed_at": datetime.utcnow().isoformat(),
                "status": "deployed"
            }
            
            # Store deployment record (you'd have a deployments table)
            logger.info(f"Deployed model version {version} with {deployment_strategy} strategy")
            
            # Update global model version
            self.model_version = version
            
            return {
                "success": True,
                "deployment": deployment_record,
                "message": f"Model version {version} deployed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deploying model: {e}")
            return {"success": False, "error": str(e)}

    async def run_training_pipeline(self) -> Dict:
        """
        Run the complete training pipeline
        """
        try:
            logger.info("Starting continuous learning pipeline")
            
            # Step 1: Collect training data
            training_data_result = await self.collect_training_data()
            
            if not training_data_result["success"]:
                return training_data_result
            
            # Step 2: Train new model
            training_result = await self.train_model(
                training_data_result["training_data"],
                training_data_result["validation_data"]
            )
            
            if not training_result["success"]:
                return training_result
            
            # Step 3: Evaluate candidates
            candidate_versions = [training_result["new_version"]]
            evaluation_result = await self.evaluate_model_candidates(
                self.model_version, 
                candidate_versions
            )
            
            if not evaluation_result["success"]:
                return evaluation_result
            
            # Step 4: Deploy if improvement is significant
            deployment_result = {"success": True, "deployed": False}
            
            if evaluation_result["should_promote"]:
                deployment_result = await self.deploy_model(
                    evaluation_result["best_candidate"]["version"],
                    "canary"
                )
            
            return {
                "success": True,
                "training_data": training_data_result,
                "training_result": training_result,
                "evaluation_result": evaluation_result,
                "deployment_result": deployment_result,
                "pipeline_completed": True
            }
            
        except Exception as e:
            logger.error(f"Error in training pipeline: {e}")
            return {"success": False, "error": str(e)}

    async def get_model_metrics(self) -> Dict:
        """
        Get current model performance metrics
        """
        try:
            # Get overall performance metrics
            performance_metrics = await feedback_service.get_model_performance_metrics()
            
            # Get recent training data for analysis
            recent_data_result = await self.collect_training_data(days_back=7)
            
            if recent_data_result["success"] and recent_data_result["test_data"]:
                test_metrics = await self.analyze_model_performance(recent_data_result["test_data"])
            else:
                test_metrics = {}
            
            return {
                "model_version": self.model_version,
                "overall_metrics": performance_metrics,
                "recent_test_metrics": test_metrics,
                "training_data_available": recent_data_result.get("sample_count", 0),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting model metrics: {e}")
            return {"error": str(e)}

# Global instance
continuous_learning_service = ContinuousLearningService()