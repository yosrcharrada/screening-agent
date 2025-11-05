# api/score_calculator.py
import logging
from typing import Dict, List
from .scoring_config import ScoringConfig
from .feature_extractors import FeatureExtractors

logger = logging.getLogger(__name__)

class ScoreCalculator:
    """Main scoring engine with XAI capabilities"""
    
    def __init__(self):
        self.config = ScoringConfig.load_config()
        self.extractors = FeatureExtractors()
    
    def calculate_comprehensive_score(self, 
                                   transcript: str,
                                   wpm: float,
                                   filler_rate: float, 
                                   answer_length_s: float,
                                   jd_keywords: List[str],
                                   question: str = "") -> Dict:
        """
        Calculate comprehensive interview score with XAI explanations
        """
        logger.info("🧮 Calculating comprehensive interview score...")
        
        # Extract all features
        features = self._extract_all_features(
            transcript, wpm, filler_rate, answer_length_s, jd_keywords, question
        )
        
        # Calculate subscores
        subscores = self._calculate_subscores(features)
        
        # Calculate final score
        final_score = self._calculate_final_score(subscores)
        
        # Generate XAI explanations
        explanations = self._generate_explanations(features, subscores, final_score)
        
        # Generate next actions
        next_actions = self._generate_next_actions(features, subscores)
        
        result = {
            "final_score": round(final_score, 2),
            "subscores": subscores,
            "feature_breakdown": features,
            "explanations": explanations,
            "next_actions": next_actions,
            "version": "1.0"
        }
        
        logger.info(f"✅ Score calculation complete: {final_score:.1f}/100")
        return result
    
    def _extract_all_features(self, transcript, wpm, filler_rate, answer_length_s, jd_keywords, question):
        """Extract all features for scoring"""
        features = {}
        
        # CONTENT FEATURES (45% of final score)
        features['star_completeness'] = self.extractors.measure_star_completeness(transcript)
        features['jd_keyword_overlap'] = self.extractors.measure_jd_keyword_overlap(transcript, jd_keywords)
        features['specificity_metric'] = self.extractors.measure_specificity_metric(transcript)
        features['relevance'] = self.extractors.measure_relevance(transcript, question)
        
        # DELIVERY FEATURES (35% of final score)  
        features['pace_wpm'] = self.extractors.measure_pace(wpm)
        features['filler_rate'] = self.extractors.measure_filler_rate(filler_rate)
        features['answer_length'] = self.extractors.measure_answer_length(answer_length_s)
        features['tone_expressiveness'] = self.extractors.measure_tone_expressiveness(transcript)
        
        # COMMUNICATION FEATURES (20% of final score)
        features['logical_flow'] = self.extractors.measure_logical_flow(transcript)
        features['clarity'] = self.extractors.measure_clarity(transcript)
        
        return features
    
    def _calculate_subscores(self, features):
        """Calculate subscores for each category"""
        subscores = {}
        
        # CONTENT subscore (45% of final score)
        content_weights = self.config['content_features']
        content_score = sum(
            features[feature]['score'] * content_weights[feature]['weight']
            for feature in content_weights
        ) * 100
        
        # Calculate individual feature contributions for XAI
        content_features_detail = {}
        for feature in content_weights:
            feature_weight = content_weights[feature]['weight']
            feature_score = features[feature]['score']
            contribution = feature_score * feature_weight * 45  # 45% of final score
            
            content_features_detail[feature] = {
                'score': round(feature_score, 2),
                'contribution': round(contribution, 1),
                'evidence': features[feature].get('evidence', ''),
                'details': {k: v for k, v in features[feature].items() if k != 'evidence'}
            }
        
        subscores['content'] = {
            'score': round(content_score, 1),
            'weight': self.config['final_score_weights']['content_weight'],
            'features': content_features_detail
        }
        
        # DELIVERY subscore (35% of final score)
        delivery_weights = self.config['delivery_features']
        delivery_score = sum(
            features[feature]['score'] * delivery_weights[feature]['weight']
            for feature in delivery_weights
        ) * 100
        
        delivery_features_detail = {}
        for feature in delivery_weights:
            feature_weight = delivery_weights[feature]['weight']
            feature_score = features[feature]['score']
            contribution = feature_score * feature_weight * 35  # 35% of final score
            
            delivery_features_detail[feature] = {
                'score': round(feature_score, 2),
                'contribution': round(contribution, 1),
                'evidence': features[feature].get('evidence', ''),
                'details': {k: v for k, v in features[feature].items() if k != 'evidence'}
            }
        
        subscores['delivery'] = {
            'score': round(delivery_score, 1),
            'weight': self.config['final_score_weights']['delivery_weight'],
            'features': delivery_features_detail
        }
        
        # COMMUNICATION subscore (20% of final score)
        communication_weights = self.config['communication_features']
        communication_score = sum(
            features[feature]['score'] * communication_weights[feature]['weight']
            for feature in communication_weights
        ) * 100
        
        communication_features_detail = {}
        for feature in communication_weights:
            feature_weight = communication_weights[feature]['weight']
            feature_score = features[feature]['score']
            contribution = feature_score * feature_weight * 20  # 20% of final score
            
            communication_features_detail[feature] = {
                'score': round(feature_score, 2),
                'contribution': round(contribution, 1),
                'evidence': features[feature].get('evidence', ''),
                'details': {k: v for k, v in features[feature].items() if k != 'evidence'}
            }
        
        subscores['communication'] = {
            'score': round(communication_score, 1),
            'weight': self.config['final_score_weights']['communication_weight'],
            'features': communication_features_detail
        }
        
        return subscores
    
    def _calculate_final_score(self, subscores):
        """Calculate final weighted score"""
        final_weights = self.config['final_score_weights']
        
        final_score = (
            subscores['content']['score'] * final_weights['content_weight'] +
            subscores['delivery']['score'] * final_weights['delivery_weight'] +
            subscores['communication']['score'] * final_weights['communication_weight']
        )
        
        return max(0, min(100, final_score))
    
    def _generate_explanations(self, features, subscores, final_score):
        """Generate XAI explanations for the score"""
        explanations = []
        
        # Content explanations (45% of score)
        star_result = features['star_completeness']
        if star_result['score'] < 0.5:
            explanations.append(f"❌ STAR structure very weak - {star_result['evidence']}")
        elif star_result['score'] < 0.75:
            explanations.append(f"⚠️ STAR structure incomplete - {star_result['evidence']}")
        else:
            explanations.append(f"✅ Strong STAR structure - {star_result['evidence']}")
            
        keyword_result = features['jd_keyword_overlap']
        if keyword_result['score'] < 0.3:
            explanations.append(f"❌ Poor JD keyword usage - {keyword_result['evidence']}")
        elif keyword_result['score'] < 0.6:
            explanations.append(f"⚠️ Limited JD keyword usage - {keyword_result['evidence']}")
        else:
            explanations.append(f"✅ Good JD keyword coverage - {keyword_result['evidence']}")
            
        if not features['specificity_metric']['has_metric']:
            explanations.append("❌ No specific metrics or numbers mentioned")
        else:
            explanations.append("✅ Used specific metrics effectively")
        
        # Delivery explanations (35% of score)
        if features['pace_wpm']['score'] < 0.6:
            explanations.append(f"❌ Pace needs major adjustment - {features['pace_wpm']['evidence']}")
        elif features['pace_wpm']['score'] < 0.8:
            explanations.append(f"⚠️ Pace needs adjustment - {features['pace_wpm']['evidence']}")
        else:
            explanations.append(f"✅ Good speaking pace - {features['pace_wpm']['evidence']}")
            
        if features['filler_rate']['score'] < 0.6:
            explanations.append(f"❌ High filler words - {features['filler_rate']['evidence']}")
        elif features['filler_rate']['score'] < 0.8:
            explanations.append(f"⚠️ Some filler words - {features['filler_rate']['evidence']}")
        else:
            explanations.append(f"✅ Controlled filler words - {features['filler_rate']['evidence']}")
        
        # Communication explanations (20% of score)
        if features['logical_flow']['score'] < 0.6:
            explanations.append(f"❌ Logical flow needs improvement - {features['logical_flow']['evidence']}")
        elif features['logical_flow']['score'] < 0.8:
            explanations.append(f"⚠️ Logical flow could improve - {features['logical_flow']['evidence']}")
        else:
            explanations.append(f"✅ Good logical structure - {features['logical_flow']['evidence']}")
            
        return explanations[:6]  # Limit to 6 explanations
    
    def _generate_next_actions(self, features, subscores):
        """Generate actionable next steps"""
        actions = []
        
        # Content improvements
        if features['star_completeness']['score'] < 0.75:
            actions.append("💪 Practice STAR method: Situation, Task, Action, Result")
            
        if features['jd_keyword_overlap']['score'] < 0.6:
            actions.append("🎯 Research job description keywords and incorporate them")
            
        if not features['specificity_metric']['has_metric']:
            actions.append("📊 Add specific numbers and metrics to your stories")
        
        # Delivery improvements
        if features['pace_wpm']['score'] < 0.8:
            ideal_range = "120-160 WPM"
            actions.append(f"⏱️ Practice speaking at {ideal_range}")
            
        if features['filler_rate']['score'] < 0.8:
            actions.append("🗣️ Practice pausing instead of using filler words")
        
        # Communication improvements
        if features['logical_flow']['score'] < 0.7:
            actions.append("🔄 Use transition words: 'first', 'then', 'as a result', 'finally'")
            
        # Overall performance
        if subscores['content']['score'] < 70:
            actions.append("📝 Focus on content quality - prepare 3-5 strong work examples")
            
        if subscores['delivery']['score'] < 70:
            actions.append("🎤 Practice delivery with mock interviews")
            
        if subscores['communication']['score'] < 70:
            actions.append("🗣️ Work on clear and structured communication")
        
        return actions[:4]  # Limit to 4 actions


# Create global instance
score_calculator = ScoreCalculator()