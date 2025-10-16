#!/usr/bin/env python3
"""
Model Training Pipeline for RoleReady
Processes user feedback and retrains models for continuous improvement
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FeedbackProcessor:
    """Processes user feedback data for model training"""
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables"""
        cursor = self.conn.cursor()
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                resume_id TEXT NOT NULL,
                team_id TEXT,
                old_text TEXT NOT NULL,
                new_text TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                section TEXT,
                confidence_score REAL,
                processing_time_ms INTEGER,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Training data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                section TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                confidence_score REAL,
                user_improvement_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                section TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def extract_training_pairs(self, days_back: int = 30) -> List[Tuple[str, str, str, str, float]]:
        """
        Extract training pairs from feedback data
        
        Returns:
            List of (input_text, output_text, section, feedback_type, improvement_score)
        """
        cursor = self.conn.cursor()
        
        # Get feedback from last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = '''
            SELECT old_text, new_text, section, feedback_type, confidence_score
            FROM feedback
            WHERE created_at >= ? AND feedback_type IN ('improvement', 'manual_edit')
            ORDER BY created_at DESC
        '''
        
        cursor.execute(query, (cutoff_date.isoformat(),))
        results = cursor.fetchall()
        
        training_pairs = []
        for old_text, new_text, section, feedback_type, confidence_score in results:
            # Calculate improvement score based on text characteristics
            improvement_score = self._calculate_improvement_score(old_text, new_text)
            
            # Only include pairs with significant improvement
            if improvement_score > 0.3:  # Threshold for meaningful improvement
                training_pairs.append((old_text, new_text, section, feedback_type, improvement_score))
        
        logger.info(f"Extracted {len(training_pairs)} training pairs from feedback")
        return training_pairs
    
    def _calculate_improvement_score(self, old_text: str, new_text: str) -> float:
        """Calculate improvement score based on text characteristics"""
        score = 0.0
        
        # Length improvement (not too short, not too long)
        length_ratio = len(new_text) / max(len(old_text), 1)
        if 0.8 <= length_ratio <= 1.5:
            score += 0.2
        
        # Quantification improvement
        old_numbers = sum(1 for c in old_text if c.isdigit())
        new_numbers = sum(1 for c in new_text if c.isdigit())
        if new_numbers > old_numbers:
            score += 0.3
        
        # Action verbs improvement
        action_verbs = ['developed', 'implemented', 'created', 'built', 'designed', 'optimized', 'improved', 'increased', 'reduced']
        old_verbs = sum(1 for verb in action_verbs if verb in old_text.lower())
        new_verbs = sum(1 for verb in action_verbs if verb in new_text.lower())
        if new_verbs > old_verbs:
            score += 0.2
        
        # Technical terms improvement
        tech_terms = ['python', 'javascript', 'react', 'aws', 'docker', 'kubernetes', 'api', 'database', 'machine learning']
        old_tech = sum(1 for term in tech_terms if term in old_text.lower())
        new_tech = sum(1 for term in tech_terms if term in new_text.lower())
        if new_tech > old_tech:
            score += 0.2
        
        # Specificity improvement (fewer generic words)
        generic_words = ['good', 'excellent', 'great', 'strong', 'effective', 'successful']
        old_generic = sum(1 for word in generic_words if word in old_text.lower())
        new_generic = sum(1 for word in generic_words if word in new_text.lower())
        if new_generic < old_generic:
            score += 0.1
        
        return min(score, 1.0)
    
    def analyze_feedback_patterns(self) -> Dict:
        """Analyze feedback patterns for insights"""
        cursor = self.conn.cursor()
        
        # Feedback by type
        cursor.execute('''
            SELECT feedback_type, COUNT(*) as count
            FROM feedback
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY feedback_type
        ''')
        feedback_by_type = dict(cursor.fetchall())
        
        # Feedback by section
        cursor.execute('''
            SELECT section, COUNT(*) as count
            FROM feedback
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY section
            ORDER BY count DESC
        ''')
        feedback_by_section = dict(cursor.fetchall())
        
        # Average confidence scores
        cursor.execute('''
            SELECT AVG(confidence_score) as avg_confidence
            FROM feedback
            WHERE created_at >= datetime('now', '-30 days')
            AND confidence_score IS NOT NULL
        ''')
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Rejection rate by confidence level
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN confidence_score > 0.8 THEN 'high'
                    WHEN confidence_score > 0.5 THEN 'medium'
                    ELSE 'low'
                END as confidence_level,
                COUNT(*) as total,
                SUM(CASE WHEN feedback_type = 'rejection' THEN 1 ELSE 0 END) as rejections
            FROM feedback
            WHERE created_at >= datetime('now', '-30 days')
            AND confidence_score IS NOT NULL
            GROUP BY confidence_level
        ''')
        
        rejection_rates = {}
        for level, total, rejections in cursor.fetchall():
            rejection_rates[level] = rejections / max(total, 1)
        
        return {
            'feedback_by_type': feedback_by_type,
            'feedback_by_section': feedback_by_section,
            'average_confidence': avg_confidence,
            'rejection_rates': rejection_rates,
            'total_feedback': sum(feedback_by_type.values()),
            'analysis_date': datetime.now().isoformat()
        }

class ModelTrainer:
    """Handles model training and evaluation"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
    
    def train_section_model(self, section: str, training_pairs: List[Tuple[str, str, str, str, float]]):
        """Train model for specific resume section"""
        
        # Filter training pairs for this section
        section_pairs = [(input_text, output_text) for input_text, output_text, sec, _, _ in training_pairs if sec == section]
        
        if len(section_pairs) < 10:
            logger.warning(f"Insufficient training data for section {section}: {len(section_pairs)} pairs")
            return None
        
        logger.info(f"Training model for section {section} with {len(section_pairs)} pairs")
        
        # Mock training process (in production, this would use actual ML models)
        model_data = {
            'section': section,
            'training_pairs': len(section_pairs),
            'model_type': 'transformer_based',
            'training_date': datetime.now().isoformat(),
            'parameters': {
                'learning_rate': 0.001,
                'batch_size': 32,
                'epochs': 10
            },
            'performance_metrics': {
                'bleu_score': np.random.uniform(0.6, 0.8),
                'rouge_score': np.random.uniform(0.7, 0.9),
                'user_satisfaction': np.random.uniform(0.75, 0.85)
            }
        }
        
        # Save model metadata
        model_file = self.model_path / f"{section}_model.json"
        with open(model_file, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Model trained for section {section} - saved to {model_file}")
        return model_file
    
    def evaluate_model_performance(self, model_version: str, test_data: List[Tuple[str, str]]) -> Dict:
        """Evaluate model performance on test data"""
        
        # Mock evaluation (in production, this would use actual evaluation metrics)
        metrics = {
            'bleu_score': np.random.uniform(0.6, 0.8),
            'rouge_score': np.random.uniform(0.7, 0.9),
            'perplexity': np.random.uniform(2.0, 5.0),
            'user_satisfaction': np.random.uniform(0.75, 0.85),
            'inference_time_ms': np.random.uniform(100, 500)
        }
        
        logger.info(f"Model {model_version} evaluation: {metrics}")
        return metrics
    
    def deploy_model(self, section: str, model_file: Path) -> bool:
        """Deploy model to production"""
        
        # Mock deployment process
        logger.info(f"Deploying model for section {section}")
        
        # In production, this would:
        # 1. Validate model performance
        # 2. Run A/B tests
        # 3. Gradually roll out to users
        # 4. Monitor performance metrics
        
        deployment_status = {
            'section': section,
            'status': 'deployed',
            'deployment_time': datetime.now().isoformat(),
            'model_file': str(model_file),
            'rollout_percentage': 100  # Start with 100% for demo
        }
        
        # Save deployment status
        deployment_file = self.model_path / f"{section}_deployment.json"
        with open(deployment_file, 'w') as f:
            json.dump(deployment_status, f, indent=2)
        
        logger.info(f"Model deployed for section {section}")
        return True

class ContinuousLearningPipeline:
    """Main pipeline for continuous learning from user feedback"""
    
    def __init__(self):
        self.feedback_processor = FeedbackProcessor()
        self.model_trainer = ModelTrainer()
    
    def run_training_cycle(self, days_back: int = 30):
        """Run a complete training cycle"""
        
        logger.info("Starting continuous learning training cycle")
        
        # Step 1: Extract training data from feedback
        training_pairs = self.feedback_processor.extract_training_pairs(days_back)
        
        if not training_pairs:
            logger.warning("No training data available")
            return
        
        # Step 2: Analyze feedback patterns
        patterns = self.feedback_processor.analyze_feedback_patterns()
        logger.info(f"Feedback patterns: {patterns}")
        
        # Step 3: Train models for each section
        sections = set(section for _, _, section, _, _ in training_pairs)
        trained_models = {}
        
        for section in sections:
            model_file = self.model_trainer.train_section_model(section, training_pairs)
            if model_file:
                trained_models[section] = model_file
        
        # Step 4: Evaluate and deploy models
        for section, model_file in trained_models.items():
            # Mock test data
            test_data = [(input_text, output_text) for input_text, output_text, sec, _, _ in training_pairs[:5] if sec == section]
            
            # Evaluate model
            metrics = self.model_trainer.evaluate_model_performance(f"{section}_v2", test_data)
            
            # Deploy if performance is good
            if metrics['user_satisfaction'] > 0.7:
                self.model_trainer.deploy_model(section, model_file)
            else:
                logger.warning(f"Model for {section} did not meet performance threshold")
        
        # Step 5: Generate training report
        self._generate_training_report(patterns, trained_models)
        
        logger.info("Training cycle completed")
    
    def _generate_training_report(self, patterns: Dict, trained_models: Dict):
        """Generate training report"""
        
        report = {
            'training_date': datetime.now().isoformat(),
            'feedback_analysis': patterns,
            'models_trained': list(trained_models.keys()),
            'training_summary': {
                'total_training_pairs': len(self.feedback_processor.extract_training_pairs()),
                'sections_trained': len(trained_models),
                'successful_deployments': len(trained_models)
            },
            'recommendations': [
                'Continue collecting feedback for underrepresented sections',
                'Monitor model performance in production',
                'Consider fine-tuning for specific user segments',
                'Implement A/B testing for new model versions'
            ]
        }
        
        report_file = Path("training_reports") / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Training report saved to {report_file}")

def main():
    """Main function to run the continuous learning pipeline"""
    
    logger.info("Starting RoleReady Continuous Learning Pipeline")
    
    pipeline = ContinuousLearningPipeline()
    
    try:
        # Run training cycle
        pipeline.run_training_cycle(days_back=30)
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
