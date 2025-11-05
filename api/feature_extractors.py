# api/feature_extractors.py
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class FeatureExtractors:
    """Extract features from transcript and metrics for scoring"""
    
    @staticmethod
    def measure_star_completeness(transcript: str) -> Dict:
        """Check STAR method completeness"""
        transcript_lower = transcript.lower()
        
        # STAR method keywords
        s_keywords = ["situation", "context", "background", "faced", "when", "where"]
        t_keywords = ["task", "goal", "objective", "needed to", "responsibility", "challenge"]
        a_keywords = ["did", "implemented", "built", "created", "developed", "led", "managed"]
        r_keywords = ["result", "outcome", "achieved", "improved", "increased", "reduced", "saved"]
        
        # Check presence of each element
        has_s = any(kw in transcript_lower for kw in s_keywords)
        has_t = any(kw in transcript_lower for kw in t_keywords)
        has_a = any(kw in transcript_lower for kw in a_keywords)
        has_r = any(kw in transcript_lower for kw in r_keywords)
        
        count = sum([has_s, has_t, has_a, has_r])
        score = count / 4.0
        
        return {
            "S": has_s,
            "T": has_t,
            "A": has_a,
            "R": has_r,
            "score": score,
            "evidence": f"Found {count}/4 STAR elements"
        }
    
    @staticmethod
    def measure_jd_keyword_overlap(transcript: str, jd_keywords: List[str]) -> Dict:
        """Measure overlap with job description keywords"""
        if not jd_keywords:
            return {"matched": 0, "total": 0, "score": 0.0, "evidence": "No JD keywords provided"}
            
        transcript_lower = transcript.lower()
        matched = sum(1 for kw in jd_keywords if kw.lower() in transcript_lower)
        total = len(jd_keywords)
        score = min(matched / total, 1.0) if total > 0 else 0.0
        
        return {
            "matched": matched,
            "total": total,
            "score": score,
            "evidence": f"Mentioned {matched}/{total} job keywords"
        }
    
    @staticmethod
    def measure_specificity_metric(transcript: str) -> Dict:
        """Check for specific metrics and numbers"""
        # Patterns for metrics: percentages, numbers, time periods, money, etc.
        metric_patterns = [
            r'\d+%',  # percentages
            r'\$\d+',  # money
            r'\d+\s*(years?|months?|weeks?|days?|hours?)',  # time periods
            r'\d+\s*(people|team members|users|customers)',  # quantities
            r'increased by \d+', r'reduced by \d+', r'improved by \d+',  # improvements
        ]
        
        has_metric = any(re.search(pattern, transcript, re.IGNORECASE) for pattern in metric_patterns)
        
        return {
            "has_metric": has_metric,
            "score": 1.0 if has_metric else 0.0,
            "evidence": "Specific metric mentioned" if has_metric else "No numbers or metrics given"
        }
    
    @staticmethod
    def measure_relevance(transcript: str, question: str) -> Dict:
        """Basic relevance scoring"""
        if not question:
            return {"score": 0.5, "evidence": "No question provided for relevance check"}
            
        # Simple keyword matching
        question_keywords = set(re.findall(r'\b\w+\b', question.lower()))
        transcript_keywords = set(re.findall(r'\b\w+\b', transcript.lower()))
        
        overlap = len(question_keywords & transcript_keywords)
        total_unique = len(question_keywords)
        
        score = overlap / total_unique if total_unique > 0 else 0.5
        
        return {
            "score": min(score, 1.0),
            "evidence": f"Answer addresses {overlap} key concepts from question"
        }
    
    @staticmethod
    def measure_pace(wpm: float) -> Dict:
        """Score speaking pace"""
        if wpm < 80:
            rating, score = "too slow", 0.5
        elif wpm < 100:
            rating, score = "slow", 0.7
        elif wpm <= 160:
            rating, score = "ideal", 1.0
        elif wpm <= 200:
            rating, score = "fast", 0.7
        else:
            rating, score = "too fast", 0.5
            
        return {
            "wpm": wpm,
            "rating": rating,
            "score": score,
            "evidence": f"{wpm} WPM is {rating} for interviews"
        }
    
    @staticmethod
    def measure_filler_rate(filler_rate: float) -> Dict:
        """Score filler word usage"""
        if filler_rate < 0.02:
            rating, score = "excellent", 1.0
        elif filler_rate < 0.05:
            rating, score = "good", 0.8
        elif filler_rate < 0.10:
            rating, score = "okay", 0.6
        else:
            rating, score = "high", 0.4
            
        return {
            "rate": filler_rate,
            "percentage": f"{filler_rate*100:.1f}%",
            "rating": rating,
            "score": max(0, score),
            "evidence": f"Filler words: {filler_rate*100:.1f}% ({rating})"
        }
    
    @staticmethod
    def measure_answer_length(duration_s: float) -> Dict:
        """Score answer length appropriateness"""
        if duration_s < 30:
            rating, score = "too short", 0.4
        elif duration_s < 60:
            rating, score = "short", 0.7
        elif duration_s <= 120:
            rating, score = "ideal", 1.0
        elif duration_s <= 180:
            rating, score = "long", 0.7
        else:
            rating, score = "too long", 0.4
            
        return {
            "duration_s": duration_s,
            "rating": rating,
            "score": score,
            "evidence": f"{duration_s}s is {rating} for interview answers"
        }
    
    @staticmethod
    def measure_tone_expressiveness(transcript: str) -> Dict:
        """Simple tone analysis based on sentence variety"""
        sentences = re.split(r'[.!?]+', transcript)
        if len(sentences) < 2:
            return {"score": 0.5, "evidence": "Limited sentence variety"}
            
        # Calculate sentence length variety
        sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
        if len(sentence_lengths) < 2:
            return {"score": 0.5, "evidence": "Limited sentence variety"}
            
        length_variance = sum((l - sum(sentence_lengths)/len(sentence_lengths))**2 for l in sentence_lengths) / len(sentence_lengths)
        score = min(length_variance / 50, 1.0)  # Normalize variance
        
        return {
            "score": score,
            "evidence": "Good sentence variety" if score > 0.7 else "Limited sentence variety"
        }
    
    @staticmethod
    def measure_logical_flow(transcript: str) -> Dict:
        """Check for logical flow and transitions"""
        transition_words = ["first", "then", "next", "after", "because", "therefore", "as a result", "finally"]
        transcript_lower = transcript.lower()
        
        transitions_found = sum(1 for word in transition_words if word in transcript_lower)
        word_count = len(transcript.split())
        
        # Score based on transitions per 100 words
        transitions_per_100 = (transitions_found / word_count) * 100 if word_count > 0 else 0
        score = min(transitions_per_100 / 5, 1.0)  # Target: 5 transitions per 100 words
        
        return {
            "transitions_found": transitions_found,
            "score": score,
            "evidence": f"Found {transitions_found} logical transitions"
        }
    
    @staticmethod
    def measure_clarity(transcript: str) -> Dict:
        """Measure clarity based on sentence structure"""
        sentences = re.split(r'[.!?]+', transcript)
        if not sentences:
            return {"score": 0.5, "evidence": "No clear sentences"}
            
        word_count = len(transcript.split())
        sentence_count = len([s for s in sentences if len(s.strip()) > 0])
        
        if sentence_count == 0:
            return {"score": 0.5, "evidence": "No clear sentences"}
            
        avg_sentence_length = word_count / sentence_count
        
        # Ideal sentence length for clarity: 15-20 words
        if 10 <= avg_sentence_length <= 25:
            score = 1.0
        elif 5 <= avg_sentence_length <= 30:
            score = 0.7
        else:
            score = 0.4
            
        return {
            "avg_sentence_length": avg_sentence_length,
            "score": score,
            "evidence": f"Average sentence length: {avg_sentence_length:.1f} words"
        }