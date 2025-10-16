"""
RLHF-Lite System for RoleReady
Reinforcement Learning from Human Feedback implementation for continuous model improvement
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RewardSignal:
    """Structure for reward signals from user interactions"""
    user_id: str
    resume_id: str
    action_type: str  # 'accept', 'reject', 'edit', 'improve'
    original_text: str
    ai_generated_text: str
    final_text: str
    reward_score: float  # -1.0 to 1.0
    confidence_score: float
    processing_time_ms: int
    context: Dict
    timestamp: datetime

@dataclass
class TrainingExample:
    """Training example for RLHF"""
    input_text: str
    ai_output: str
    human_preferred_output: str
    reward_signal: float
    section: str
    metadata: Dict

class RewardModel:
    """Learns to predict user preferences from feedback"""
    
    def __init__(self, model_path: str = "models/reward_model.json"):
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        self.reward_weights = {
            'acceptance_rate': 0.3,
            'edit_distance': 0.2,
            'user_satisfaction': 0.3,
            'confidence_alignment': 0.2
        }
        self.load_model()
    
    def calculate_reward(self, reward_signal: RewardSignal) -> float:
        """Calculate reward score from user interaction"""
        
        # Base reward from action type
        action_rewards = {
            'accept': 1.0,
            'edit': 0.5,
            'improve': 0.7,
            'reject': -0.5
        }
        
        base_reward = action_rewards.get(reward_signal.action_type, 0.0)
        
        # Edit distance penalty (less editing = higher reward)
        edit_distance = self._calculate_edit_distance(
            reward_signal.ai_generated_text,
            reward_signal.final_text
        )
        edit_penalty = -edit_distance * 0.1
        
        # Confidence alignment bonus
        confidence_bonus = 0.0
        if reward_signal.action_type == 'accept':
            confidence_bonus = reward_signal.confidence_score * 0.2
        
        # Processing time penalty (faster = better)
        time_penalty = -min(reward_signal.processing_time_ms / 10000, 0.1)
        
        total_reward = base_reward + edit_penalty + confidence_bonus + time_penalty
        
        # Normalize to [-1, 1] range
        return max(-1.0, min(1.0, total_reward))
    
    def _calculate_edit_distance(self, text1: str, text2: str) -> float:
        """Calculate normalized edit distance between two texts"""
        # Simple Levenshtein distance implementation
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        # Normalize by max length
        max_len = max(m, n)
        return dp[m][n] / max_len if max_len > 0 else 0
    
    def update_weights(self, training_examples: List[TrainingExample]):
        """Update reward model weights based on training examples"""
        
        if not training_examples:
            return
        
        # Calculate gradients for weight updates
        gradients = {
            'acceptance_rate': 0.0,
            'edit_distance': 0.0,
            'user_satisfaction': 0.0,
            'confidence_alignment': 0.0
        }
        
        for example in training_examples:
            predicted_reward = self.predict_reward(example)
            error = example.reward_signal - predicted_reward
            
            # Update gradients (simplified gradient descent)
            gradients['acceptance_rate'] += error * 0.01
            gradients['edit_distance'] += error * 0.01
            gradients['user_satisfaction'] += error * 0.01
            gradients['confidence_alignment'] += error * 0.01
        
        # Update weights
        learning_rate = 0.001
        for key in self.reward_weights:
            self.reward_weights[key] += gradients[key] * learning_rate
            self.reward_weights[key] = max(0.0, min(1.0, self.reward_weights[key]))
        
        # Normalize weights
        total = sum(self.reward_weights.values())
        if total > 0:
            for key in self.reward_weights:
                self.reward_weights[key] /= total
        
        self.save_model()
        logger.info(f"Updated reward model weights: {self.reward_weights}")
    
    def predict_reward(self, example: TrainingExample) -> float:
        """Predict reward for a given example"""
        # Simplified reward prediction based on current weights
        features = self._extract_features(example)
        
        predicted_reward = 0.0
        for feature, weight in self.reward_weights.items():
            if feature in features:
                predicted_reward += features[feature] * weight
        
        return max(-1.0, min(1.0, predicted_reward))
    
    def _extract_features(self, example: TrainingExample) -> Dict[str, float]:
        """Extract features from training example"""
        
        # Acceptance rate feature (simplified)
        acceptance_rate = 1.0 if example.reward_signal > 0.5 else 0.0
        
        # Edit distance feature
        edit_distance = self._calculate_edit_distance(
            example.ai_output,
            example.human_preferred_output
        )
        
        # User satisfaction feature (based on reward signal)
        user_satisfaction = max(0.0, example.reward_signal)
        
        # Confidence alignment feature
        confidence_alignment = 0.5  # Default, would be calculated from actual confidence scores
        
        return {
            'acceptance_rate': acceptance_rate,
            'edit_distance': 1.0 - edit_distance,  # Inverse of edit distance
            'user_satisfaction': user_satisfaction,
            'confidence_alignment': confidence_alignment
        }
    
    def save_model(self):
        """Save reward model to disk"""
        model_data = {
            'weights': self.reward_weights,
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(self.model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self):
        """Load reward model from disk"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'r') as f:
                    model_data = json.load(f)
                self.reward_weights = model_data.get('weights', self.reward_weights)
                logger.info(f"Loaded reward model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load reward model: {e}")

class PolicyModel:
    """Learns optimal policy for resume generation"""
    
    def __init__(self, model_path: str = "models/policy_model.json"):
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        self.policy_weights = {
            'length_preference': 0.5,
            'technical_detail': 0.7,
            'quantification': 0.8,
            'action_verbs': 0.6,
            'specificity': 0.9
        }
        self.load_model()
    
    def update_policy(self, reward_signals: List[RewardSignal]):
        """Update policy based on reward signals"""
        
        if not reward_signals:
            return
        
        # Calculate policy gradients
        gradients = {key: 0.0 for key in self.policy_weights}
        
        for signal in reward_signals:
            # Extract policy features from the interaction
            features = self._extract_policy_features(signal)
            
            # Calculate gradient based on reward
            for feature, value in features.items():
                if feature in gradients:
                    gradients[feature] += signal.reward_score * value * 0.01
        
        # Update policy weights
        learning_rate = 0.001
        for key in self.policy_weights:
            self.policy_weights[key] += gradients[key] * learning_rate
            self.policy_weights[key] = max(0.0, min(1.0, self.policy_weights[key]))
        
        # Normalize weights
        total = sum(self.policy_weights.values())
        if total > 0:
            for key in self.policy_weights:
                self.policy_weights[key] /= total
        
        self.save_model()
        logger.info(f"Updated policy model weights: {self.policy_weights}")
    
    def _extract_policy_features(self, signal: RewardSignal) -> Dict[str, float]:
        """Extract policy features from reward signal"""
        
        ai_text = signal.ai_generated_text.lower()
        final_text = signal.final_text.lower()
        
        # Length preference
        length_ratio = len(final_text) / max(len(ai_text), 1)
        length_preference = 1.0 if 0.8 <= length_ratio <= 1.2 else 0.0
        
        # Technical detail preference
        tech_terms = ['python', 'javascript', 'aws', 'docker', 'kubernetes', 'api', 'database']
        ai_tech_count = sum(1 for term in tech_terms if term in ai_text)
        final_tech_count = sum(1 for term in tech_terms if term in final_text)
        technical_detail = 1.0 if final_tech_count >= ai_tech_count else 0.0
        
        # Quantification preference
        ai_numbers = sum(1 for c in signal.ai_generated_text if c.isdigit())
        final_numbers = sum(1 for c in signal.final_text if c.isdigit())
        quantification = 1.0 if final_numbers >= ai_numbers else 0.0
        
        # Action verbs preference
        action_verbs = ['developed', 'implemented', 'created', 'built', 'designed', 'optimized']
        ai_verbs = sum(1 for verb in action_verbs if verb in ai_text)
        final_verbs = sum(1 for verb in action_verbs if verb in final_text)
        action_verbs_pref = 1.0 if final_verbs >= ai_verbs else 0.0
        
        # Specificity preference (fewer generic words)
        generic_words = ['good', 'excellent', 'great', 'strong', 'effective']
        ai_generic = sum(1 for word in generic_words if word in ai_text)
        final_generic = sum(1 for word in generic_words if word in final_text)
        specificity = 1.0 if final_generic <= ai_generic else 0.0
        
        return {
            'length_preference': length_preference,
            'technical_detail': technical_detail,
            'quantification': quantification,
            'action_verbs': action_verbs_pref,
            'specificity': specificity
        }
    
    def get_generation_preferences(self) -> Dict[str, float]:
        """Get current generation preferences for the policy"""
        return self.policy_weights.copy()
    
    def save_model(self):
        """Save policy model to disk"""
        model_data = {
            'weights': self.policy_weights,
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(self.model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self):
        """Load policy model from disk"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'r') as f:
                    model_data = json.load(f)
                self.policy_weights = model_data.get('weights', self.policy_weights)
                logger.info(f"Loaded policy model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load policy model: {e}")

class RLHFLiteSystem:
    """Main RLHF-Lite system for continuous learning"""
    
    def __init__(self):
        self.reward_model = RewardModel()
        self.policy_model = PolicyModel()
        self.training_buffer = []
        self.buffer_size = 1000
    
    def record_user_interaction(
        self,
        user_id: str,
        resume_id: str,
        action_type: str,
        original_text: str,
        ai_generated_text: str,
        final_text: str,
        confidence_score: float,
        processing_time_ms: int,
        context: Dict = None
    ) -> float:
        """Record user interaction and calculate reward"""
        
        # Create reward signal
        reward_signal = RewardSignal(
            user_id=user_id,
            resume_id=resume_id,
            action_type=action_type,
            original_text=original_text,
            ai_generated_text=ai_generated_text,
            final_text=final_text,
            reward_score=0.0,  # Will be calculated
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            context=context or {},
            timestamp=datetime.now()
        )
        
        # Calculate reward
        reward_score = self.reward_model.calculate_reward(reward_signal)
        reward_signal.reward_score = reward_score
        
        # Add to training buffer
        self.training_buffer.append(reward_signal)
        
        # Keep buffer size manageable
        if len(self.training_buffer) > self.buffer_size:
            self.training_buffer = self.training_buffer[-self.buffer_size:]
        
        logger.info(f"Recorded interaction: {action_type}, reward: {reward_score:.3f}")
        
        return reward_score
    
    def update_models(self):
        """Update both reward and policy models"""
        
        if len(self.training_buffer) < 10:
            logger.warning("Insufficient training data for model update")
            return
        
        logger.info(f"Updating models with {len(self.training_buffer)} interactions")
        
        # Update reward model
        training_examples = []
        for signal in self.training_buffer:
            example = TrainingExample(
                input_text=signal.original_text,
                ai_output=signal.ai_generated_text,
                human_preferred_output=signal.final_text,
                reward_signal=signal.reward_score,
                section=signal.context.get('section', 'unknown'),
                metadata=signal.context
            )
            training_examples.append(example)
        
        self.reward_model.update_weights(training_examples)
        
        # Update policy model
        self.policy_model.update_policy(self.training_buffer)
        
        logger.info("Models updated successfully")
    
    def get_model_insights(self) -> Dict:
        """Get insights about model performance and user preferences"""
        
        if not self.training_buffer:
            return {'error': 'No training data available'}
        
        # Calculate statistics
        total_interactions = len(self.training_buffer)
        avg_reward = np.mean([s.reward_score for s in self.training_buffer])
        
        action_counts = {}
        for signal in self.training_buffer:
            action_counts[signal.action_type] = action_counts.get(signal.action_type, 0) + 1
        
        # Calculate acceptance rate
        acceptance_rate = action_counts.get('accept', 0) / total_interactions
        
        # Get current model preferences
        policy_preferences = self.policy_model.get_generation_preferences()
        reward_weights = self.reward_model.reward_weights
        
        return {
            'total_interactions': total_interactions,
            'average_reward': avg_reward,
            'acceptance_rate': acceptance_rate,
            'action_distribution': action_counts,
            'policy_preferences': policy_preferences,
            'reward_weights': reward_weights,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_generation_guidelines(self) -> Dict[str, str]:
        """Get current generation guidelines based on learned preferences"""
        
        preferences = self.policy_model.get_generation_preferences()
        
        guidelines = []
        
        if preferences['quantification'] > 0.7:
            guidelines.append("Include quantified metrics and specific numbers")
        
        if preferences['technical_detail'] > 0.7:
            guidelines.append("Add technical terminology and specific technologies")
        
        if preferences['action_verbs'] > 0.6:
            guidelines.append("Use strong action verbs in descriptions")
        
        if preferences['specificity'] > 0.8:
            guidelines.append("Avoid generic phrases, be specific and concrete")
        
        if preferences['length_preference'] > 0.6:
            guidelines.append("Maintain appropriate length (not too short or long)")
        
        return {
            'guidelines': guidelines,
            'confidence': 'high' if len(guidelines) >= 3 else 'medium',
            'last_updated': datetime.now().isoformat()
        }

# Global RLHF system instance
rlhf_system = RLHFLiteSystem()

# Convenience functions
def record_interaction(
    user_id: str,
    resume_id: str,
    action_type: str,
    original_text: str,
    ai_generated_text: str,
    final_text: str,
    confidence_score: float = 0.5,
    processing_time_ms: int = 1000,
    context: Dict = None
) -> float:
    """Record user interaction with RLHF system"""
    return rlhf_system.record_user_interaction(
        user_id=user_id,
        resume_id=resume_id,
        action_type=action_type,
        original_text=original_text,
        ai_generated_text=ai_generated_text,
        final_text=final_text,
        confidence_score=confidence_score,
        processing_time_ms=processing_time_ms,
        context=context
    )

def update_rlhf_models():
    """Update RLHF models with recent interactions"""
    rlhf_system.update_models()

def get_rlhf_insights() -> Dict:
    """Get RLHF system insights"""
    return rlhf_system.get_model_insights()

def get_generation_guidelines() -> Dict[str, str]:
    """Get current generation guidelines"""
    return rlhf_system.get_generation_guidelines()
