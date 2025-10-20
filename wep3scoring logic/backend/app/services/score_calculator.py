import yaml
from pathlib import Path
from typing import Dict, List
from .feature_extractors import (
    measure_star_completeness, measure_jd_keyword_overlap, measure_specificity_metric,
    measure_relevance, measure_pace, measure_filler_rate, measure_answer_length,
    measure_tone_expressiveness, measure_logical_flow, measure_clarity
)

def load_config():
    """Load weights.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config" / "weights.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_score(
    transcript: str,
    wpm: float,
    filler_rate: float,
    answer_length_s: float,
    jd_keywords: List[str],
    question: str
) -> Dict:
    """
    Main scoring function.
    Combines all 9 features into Content/Delivery/Communication subscores and a final score.
    """
    
    config = load_config()
    
    # ============================================
    # STEP 1: Measure all 9 features
    # ============================================
    
    # Content features
    star_result = measure_star_completeness(transcript)
    keyword_result = measure_jd_keyword_overlap(transcript, jd_keywords)
    metric_result = measure_specificity_metric(transcript)
    relevance_result = measure_relevance(transcript, question)
    
    # Delivery features
    pace_result = measure_pace(wpm)
    filler_result = measure_filler_rate(filler_rate)
    length_result = measure_answer_length(answer_length_s)
    tone_result = measure_tone_expressiveness(transcript)
    
    # Communication features
    flow_result = measure_logical_flow(transcript)
    clarity_result = measure_clarity(transcript)
    
    # ============================================
    # STEP 2: Calculate subscores (0-100)
    # ============================================
    
    # CONTENT SUBSCORE
    content_subscore = (
        star_result['score'] * 0.35 +
        keyword_result['score'] * 0.25 +
        metric_result['score'] * 0.20 +
        relevance_result['score'] * 0.20
    ) * 100
    
    # DELIVERY SUBSCORE
    delivery_subscore = (
        pace_result['score'] * 0.30 +
        filler_result['score'] * 0.25 +
        length_result['score'] * 0.25 +
        tone_result['score'] * 0.20
    ) * 100
    
    # COMMUNICATION SUBSCORE
    communication_subscore = (
        flow_result['score'] * 0.50 +
        clarity_result['score'] * 0.50
    ) * 100
    
    # ============================================
    # STEP 3: Calculate FINAL SCORE (0-100)
    # ============================================
    
    final_score = (
        content_subscore * 0.45 +
        delivery_subscore * 0.35 +
        communication_subscore * 0.20
    ) 
    
    # ============================================
    # STEP 4: Calculate contributions (XAI)
    # ============================================
    
    contributions = {
        'content': {
            'score': round(content_subscore, 1),
            'weight': 0.45,
            'features': {
                'star': {
                    'score': round(star_result['score'], 2),
                    'contribution': round(star_result['score'] * 0.35 * 45, 1),
                    'evidence': star_result['evidence']
                },
                'keywords': {
                    'score': round(keyword_result['score'], 2),
                    'contribution': round(keyword_result['score'] * 0.25 * 45, 1),
                    'evidence': keyword_result['evidence']
                },
                'metric': {
                    'score': round(metric_result['score'], 2),
                    'contribution': round(metric_result['score'] * 0.20 * 45, 1),
                    'evidence': metric_result['evidence']
                },
                'relevance': {
                    'score': round(relevance_result['score'], 2),
                    'contribution': round(relevance_result['score'] * 0.20 * 45, 1),
                    'evidence': relevance_result['evidence']
                },
            }
        },
        'delivery': {
            'score': round(delivery_subscore, 1),
            'weight': 0.35,
            'features': {
                'pace': {
                    'score': round(pace_result['score'], 2),
                    'contribution': round(pace_result['score'] * 0.30 * 35, 1),
                    'evidence': pace_result['evidence']
                },
                'filler': {
                    'score': round(filler_result['score'], 2),
                    'contribution': round(filler_result['score'] * 0.25 * 35, 1),
                    'evidence': filler_result['evidence']
                },
                'length': {
                    'score': round(length_result['score'], 2),
                    'contribution': round(length_result['score'] * 0.25 * 35, 1),
                    'evidence': length_result['evidence']
                },
                'tone': {
                    'score': round(tone_result['score'], 2),
                    'contribution': round(tone_result['score'] * 0.20 * 35, 1),
                    'evidence': tone_result['evidence']
                },
            }
        },
        'communication': {
            'score': round(communication_subscore, 1),
            'weight': 0.20,
            'features': {
                'flow': {
                    'score': round(flow_result['score'], 2),
                    'contribution': round(flow_result['score'] * 0.50 * 20, 1),
                    'evidence': flow_result['evidence']
                },
                'clarity': {
                    'score': round(clarity_result['score'], 2),
                    'contribution': round(clarity_result['score'] * 0.50 * 20, 1),
                    'evidence': clarity_result['evidence']
                },
            }
        }
    }
    
    # ============================================
    # STEP 5: Generate evidence bullets
    # ============================================
    
    evidence = []
    
    if star_result['score'] < 0.75:
        evidence.append(f"✓ STAR structure incomplete — {star_result['evidence']}")
    else:
        evidence.append(f"✓ Strong STAR structure — all elements present")
    
    if keyword_result['score'] > 0.6:
        evidence.append(f"✓ Good job using job keywords — {keyword_result['evidence']}")
    else:
        evidence.append(f"⚠ Could use more job-specific keywords — {keyword_result['evidence']}")
    
    if pace_result['score'] < 0.8:
        evidence.append(f"⚠ Speaking pace needs adjustment — {pace_result['evidence']}")
    else:
        evidence.append(f"✓ Speaking pace is good — {pace_result['evidence']}")
    
    if filler_result['score'] < 0.8:
        evidence.append(f"⚠ Reduce filler words — {filler_result['evidence']}")
    else:
        evidence.append(f"✓ Good control of filler words — {filler_result['evidence']}")
    
    # ============================================
    # STEP 6: Generate next actions
    # ============================================
    
    next_actions = []
    
    if star_result['score'] < 0.75:
        next_actions.append("💪 Next step: Practice STAR structure on 3 different stories")
    
    if keyword_result['score'] < 0.6:
        next_actions.append("💪 Next step: Review job description and practice weaving key terms into your answers")
    
    if pace_result['score'] < 0.8:
        next_actions.append(f"💪 Next step: Practice speaking at 140 WPM by reading practice texts aloud")
    
    if filler_result['score'] < 0.8:
        next_actions.append("💪 Next step: Practice pausing for 2 seconds instead of saying 'um' or 'uh'")
    
    if length_result['score'] < 0.8:
        next_actions.append(f"💪 Next step: Add more context and examples to reach 60-120 seconds")
    
    # ============================================
    # STEP 7: Build final response
    # ============================================
    
    return {
        'final_score': round(final_score, 2),
        'content': contributions['content'],
        'delivery': contributions['delivery'],
        'communication': contributions['communication'],
        'evidence': evidence[:5],  # Max 5 bullets
        'next_actions': next_actions[:3],  # Max 3 actions
    }