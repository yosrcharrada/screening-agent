# api/scoring_config.py
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ScoringConfig:
    """Configuration for the scoring system"""
    
    DEFAULT_WEIGHTS = {
        'final_score_weights': {
            'content_weight': 0.45,      # 45% - Most important
            'delivery_weight': 0.35,     # 35% - Second most important  
            'communication_weight': 0.20 # 20% - Third most important
        },
        'content_features': {
            'star_completeness': {'weight': 0.35},  # 35% of content score
            'jd_keyword_overlap': {'weight': 0.25}, # 25% of content score
            'specificity_metric': {'weight': 0.20}, # 20% of content score
            'relevance': {'weight': 0.20}           # 20% of content score
        },
        'delivery_features': {
            'pace_wpm': {'weight': 0.30},
            'filler_rate': {'weight': 0.25},
            'answer_length': {'weight': 0.25},
            'tone_expressiveness': {'weight': 0.20}
        },
        'communication_features': {
            'logical_flow': {'weight': 0.50},
            'clarity': {'weight': 0.50}
        }
    }
    
    @classmethod
    def load_config(cls):
        """Load configuration - for now returns default weights"""
        logger.info("📊 Loading scoring configuration...")
        return cls.DEFAULT_WEIGHTS