# api/score_calculator.py - FIXED LLM INTEGRATION
import logging
from typing import Dict, List
from .scoring_config import ScoringConfig
from .feature_extractors import FeatureExtractors
from .llm_service import llm_service

logger = logging.getLogger(__name__)

class ScoreCalculator:
    """Main scoring engine with XAI capabilities"""
    
    def __init__(self):
        self.config = ScoringConfig.load_config()
        self.extractors = FeatureExtractors()
        logger.info("✅ ScoreCalculator initialized with LLM service")
    
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
        logger.info("🧮 Starting comprehensive score calculation...")
        
        try:
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
            
            # Create base result
            result = {
                "final_score": round(final_score, 2),
                "subscores": subscores,
                "feature_breakdown": features,
                "explanations": explanations,
                "next_actions": next_actions,
                "version": "1.0"
            }
            
            # ✅ FIXED: Enhanced LLM explanation with better error handling
            logger.info("🤖 Attempting to generate LLM explanation...")
            
            try:
                llm_explanation = llm_service.generate_natural_explanation(result)
                
                if llm_explanation and "fallback" not in llm_explanation.lower():
                    result["llm_explanation"] = llm_explanation
                    result["llm_status"] = "success"
                    result["llm_model"] = getattr(llm_service, 'fast_model', 'unknown')
                    logger.info("🎉 LLM explanation successfully integrated")
                else:
                    result["llm_explanation"] = llm_service._get_fallback_explanation(result)
                    result["llm_status"] = "fallback_used"
                    logger.info("ℹ️ Using enhanced fallback explanation")
                    
            except Exception as llm_error:
                logger.error(f"❌ LLM explanation failed: {llm_error}")
                result["llm_explanation"] = llm_service._get_fallback_explanation(result)
                result["llm_status"] = "error_fallback"
                result["llm_error"] = str(llm_error)
            
            logger.info(f"✅ Score calculation complete: {final_score:.1f}/100")
            return result
            
        except Exception as e:
            logger.error(f"❌ Comprehensive score calculation failed: {e}")
            return self._get_error_fallback(str(e))
    
    def _extract_all_features(self, transcript, wpm, filler_rate, answer_length_s, jd_keywords, question):
        """Extract all features for scoring"""
        logger.info("🔍 Extracting features from transcript and metrics...")
        
        features = {}
        
        try:
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
            
            logger.info("✅ All features extracted successfully")
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            # Return default features to prevent complete failure
            return self._get_default_features(wpm, filler_rate, answer_length_s)
    
    def _get_default_features(self, wpm, filler_rate, answer_length_s):
        """Provide default features when extraction fails"""
        return {
            'star_completeness': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'jd_keyword_overlap': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'specificity_metric': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'relevance': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'pace_wpm': {'score': 0.5, 'evidence': 'Feature extraction failed', 'wpm': wpm},
            'filler_rate': {'score': 0.5, 'evidence': 'Feature extraction failed', 'rate': filler_rate},
            'answer_length': {'score': 0.5, 'evidence': 'Feature extraction failed', 'duration_s': answer_length_s},
            'tone_expressiveness': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'logical_flow': {'score': 0.5, 'evidence': 'Feature extraction failed'},
            'clarity': {'score': 0.5, 'evidence': 'Feature extraction failed'}
        }
    
    def _calculate_subscores(self, features):
        """Calculate subscores for each category"""
        try:
            subscores = {}
            
            # CONTENT subscore (45% of final score)
            content_weights = self.config['content_features']
            content_score = sum(
                features[feature]['score'] * content_weights[feature]['weight']
                for feature in content_weights
            ) * 100
            
            content_features_detail = {}
            for feature in content_weights:
                feature_weight = content_weights[feature]['weight']
                feature_score = features[feature]['score']
                contribution = feature_score * feature_weight * 45
                
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
                contribution = feature_score * feature_weight * 35
                
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
                contribution = feature_score * feature_weight * 20
                
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
            
            logger.info("✅ Subscores calculated successfully")
            return subscores
            
        except Exception as e:
            logger.error(f"❌ Subscore calculation failed: {e}")
            # Return default subscores to prevent complete failure
            return self._get_default_subscores()
    
    def _get_default_subscores(self):
        """Provide default subscores when calculation fails"""
        return {
            'content': {
                'score': 50.0,
                'weight': 0.45,
                'features': {}
            },
            'delivery': {
                'score': 50.0, 
                'weight': 0.35,
                'features': {}
            },
            'communication': {
                'score': 50.0,
                'weight': 0.20,
                'features': {}
            }
        }
    
    def _calculate_final_score(self, subscores):
        """Calculate final weighted score"""
        try:
            final_weights = self.config['final_score_weights']
            
            final_score = (
                subscores['content']['score'] * final_weights['content_weight'] +
                subscores['delivery']['score'] * final_weights['delivery_weight'] +
                subscores['communication']['score'] * final_weights['communication_weight']
            )
            
            return max(0, min(100, round(final_score, 2)))
            
        except Exception as e:
            logger.error(f"❌ Final score calculation failed: {e}")
            return 50.0  # Default score
    
    def _generate_explanations(self, features, subscores, final_score):
        """Generate XAI explanations for the score"""
        try:
            explanations = []
            
            # Content explanations
            star_result = features['star_completeness']
            if star_result['score'] < 0.5:
                explanations.append(f"❌ STAR structure needs work - {star_result['evidence']}")
            elif star_result['score'] < 0.75:
                explanations.append(f"⚠️ STAR structure partially complete - {star_result['evidence']}")
            else:
                explanations.append(f"✅ Strong STAR structure - {star_result['evidence']}")
                
            keyword_result = features['jd_keyword_overlap']
            if keyword_result['score'] < 0.3:
                explanations.append(f"❌ Limited JD keyword usage - {keyword_result['evidence']}")
            elif keyword_result['score'] < 0.6:
                explanations.append(f"⚠️ Moderate JD keyword coverage - {keyword_result['evidence']}")
            else:
                explanations.append(f"✅ Good JD keyword alignment - {keyword_result['evidence']}")
                
            if not features['specificity_metric']['has_metric']:
                explanations.append("❌ Add specific metrics and numbers to strengthen answers")
            else:
                explanations.append("✅ Used concrete metrics effectively")
            
            # Delivery explanations
            if features['pace_wpm']['score'] < 0.6:
                explanations.append(f"❌ Speaking pace needs adjustment - {features['pace_wpm']['evidence']}")
            elif features['pace_wpm']['score'] < 0.8:
                explanations.append(f"⚠️ Pace could be optimized - {features['pace_wpm']['evidence']}")
            else:
                explanations.append(f"✅ Excellent speaking pace - {features['pace_wpm']['evidence']}")
                
            if features['filler_rate']['score'] < 0.6:
                explanations.append(f"❌ High filler word usage - {features['filler_rate']['evidence']}")
            elif features['filler_rate']['score'] < 0.8:
                explanations.append(f"⚠️ Some filler words present - {features['filler_rate']['evidence']}")
            else:
                explanations.append(f"✅ Clean speech with minimal fillers - {features['filler_rate']['evidence']}")
            
            # Communication explanations
            if features['logical_flow']['score'] < 0.6:
                explanations.append(f"❌ Logical flow needs improvement - {features['logical_flow']['evidence']}")
            elif features['logical_flow']['score'] < 0.8:
                explanations.append(f"⚠️ Logical structure could be clearer - {features['logical_flow']['evidence']}")
            else:
                explanations.append(f"✅ Clear logical progression - {features['logical_flow']['evidence']}")
                
            return explanations[:6]  # Limit to 6 explanations
            
        except Exception as e:
            logger.error(f"❌ Explanation generation failed: {e}")
            return ["Analysis temporarily unavailable - using basic scoring"]
    
    def _generate_next_actions(self, features, subscores):
        """Generate actionable next steps"""
        try:
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
                actions.append("⏱️ Practice speaking at 120-160 WPM")
                
            if features['filler_rate']['score'] < 0.8:
                actions.append("🗣️ Practice pausing instead of using filler words")
            
            # Communication improvements
            if features['logical_flow']['score'] < 0.7:
                actions.append("🔄 Use transition words: 'first', 'then', 'as a result', 'finally'")
                
            # Overall category improvements
            if subscores['content']['score'] < 70:
                actions.append("📝 Focus on content quality - prepare 3-5 strong work examples")
                
            if subscores['delivery']['score'] < 70:
                actions.append("🎤 Practice delivery with mock interviews")
                
            if subscores['communication']['score'] < 70:
                actions.append("🗣️ Work on clear and structured communication")
            
            # Ensure we have at least 2 actions
            if len(actions) < 2:
                actions.extend([
                    "📚 Review common interview questions and practice answers",
                    "🎯 Focus on connecting your experience to the job requirements"
                ])
            
            return actions[:4]  # Limit to 4 actions
            
        except Exception as e:
            logger.error(f"❌ Next actions generation failed: {e}")
            return [
                "Practice with more mock interviews",
                "Review your answers for clarity and structure"
            ]
    
    def _get_error_fallback(self, error_message):
        """Provide comprehensive fallback when scoring fails"""
        logger.error(f"🔴 Scoring system failed, using fallback: {error_message}")
        
        return {
            "final_score": 50.0,
            "subscores": {
                "content": {
                    "score": 50.0,
                    "weight": 0.45,
                    "features": {}
                },
                "delivery": {
                    "score": 50.0,
                    "weight": 0.35, 
                    "features": {}
                },
                "communication": {
                    "score": 50.0,
                    "weight": 0.20,
                    "features": {}
                }
            },
            "feature_breakdown": {},
            "explanations": [
                "Scoring system encountered an error",
                "Using fallback scoring mechanism"
            ],
            "next_actions": [
                "Please try recording your answer again",
                "Ensure clear audio quality for better analysis"
            ],
            "llm_explanation": "We're experiencing technical difficulties with our analysis system. Your interview practice is still valuable - focus on clear communication and structured answers using the STAR method.",
            "llm_status": "system_error",
            "version": "1.0-fallback"
        }

# Create global instance
score_calculator = ScoreCalculator()