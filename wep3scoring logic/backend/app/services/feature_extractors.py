import re
from typing import List

# ============================================
# CONTENT FEATURES
# ============================================

def measure_star_completeness(transcript: str) -> dict:
    """
    Check if Situation, Task, Action, Result are all present.
    Returns: {"S": bool, "T": bool, "A": bool, "R": bool, "score": 0-1}
    """
    transcript_lower = transcript.lower()
    
    # Keywords for each STAR element
    s_keywords = ["situation", "context", "background", "was asked", "faced", "when"]
    t_keywords = ["task", "goal", "objective", "needed to", "had to"]
    a_keywords = ["did", "implemented", "built", "created", "developed"]
    r_keywords = ["result", "outcome", "achieved", "improved", "reduced"]
    
    has_s = any(kw in transcript_lower for kw in s_keywords)
    has_t = any(kw in transcript_lower for kw in t_keywords)
    has_a = any(kw in transcript_lower for kw in a_keywords)
    has_r = any(kw in transcript_lower for kw in r_keywords)
    
    count = sum([has_s, has_t, has_a, has_r])
    score = count / 4.0  # 0 to 1
    
    return {
        "S": has_s,
        "T": has_t,
        "A": has_a,
        "R": has_r,
        "score": score,
        "evidence": f"Found {count}/4 STAR elements"
    }

def measure_jd_keyword_overlap(transcript: str, jd_keywords: List[str]) -> dict:
    """
    Count how many JD keywords appear in the transcript.
    Returns: {"matched": int, "total": int, "score": 0-1}
    """
    transcript_lower = transcript.lower()
    matched = sum(1 for kw in jd_keywords if kw.lower() in transcript_lower)
    total = len(jd_keywords) if jd_keywords else 1
    score = min(matched / total, 1.0)
    
    return {
        "matched": matched,
        "total": total,
        "score": score,
        "evidence": f"Mentioned {matched}/{total} job keywords"
    }

def measure_specificity_metric(transcript: str) -> dict:
    """
    Check if specific numbers or metrics are mentioned.
    Returns: {"has_metric": bool, "score": 0 or 1}
    """
    # Look for patterns like "30%", "$5M", "2 weeks"
    has_metric = bool(re.search(
        r'\d+%|\d+\s*(hours?|days?|weeks?|months?|years?|users?|customers?|dollars?|\$)',
        transcript
    ))
    
    return {
        "has_metric": has_metric,
        "score": 1.0 if has_metric else 0.0,
        "evidence": "Specific metric mentioned" if has_metric else "No specific numbers given"
    }

def measure_relevance(transcript: str, question: str) -> dict:
    """
    Check if answer is relevant to the question.
    Returns: {"overlap": float, "score": 0-1}
    """
    q_words = set(question.lower().split())
    t_words = set(transcript.lower().split())
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'was', 'to', 'i', 'you'}
    q_words -= stop_words
    
    overlap = len(q_words & t_words) / max(len(q_words), 1)
    score = min(overlap, 1.0)
    
    return {
        "overlap": overlap,
        "score": score,
        "evidence": f"Answer addresses {int(overlap*100)}% of question keywords"
    }

# ============================================
# DELIVERY FEATURES
# ============================================

def measure_pace(wpm: float) -> dict:
    """
    Score speaking pace. Ideal: 120-160 WPM.
    Returns: {"wpm": float, "rating": str, "score": 0-1}
    """
    if wpm < 80:
        return {"wpm": wpm, "rating": "too slow", "score": 0.5, "evidence": f"{wpm} WPM is too slow"}
    elif wpm > 200:
        return {"wpm": wpm, "rating": "too fast", "score": 0.5, "evidence": f"{wpm} WPM is too fast"}
    elif 120 <= wpm <= 160:
        return {"wpm": wpm, "rating": "ideal", "score": 1.0, "evidence": f"{wpm} WPM is ideal"}
    elif wpm < 120:
        gap = 120 - wpm
        score = 0.5 + (gap / 40) * 0.5
        return {"wpm": wpm, "rating": "slow", "score": score, "evidence": f"{wpm} WPM could be faster"}
    else:  # wpm > 160
        gap = wpm - 160
        score = 0.5 + (gap / 40) * 0.5
        return {"wpm": wpm, "rating": "fast", "score": min(score, 1.0), "evidence": f"{wpm} WPM is a bit fast"}

def measure_filler_rate(filler_rate: float) -> dict:
    """
    Score filler words. Lower is better.
    filler_rate: decimal (0.05 = 5%)
    Returns: {"rate": float, "percentage": str, "score": 0-1}
    """
    score = max(0, 1.0 - (filler_rate * 10))  # Each 10% filler reduces score
    
    if filler_rate < 0.02:
        rating = "excellent"
    elif filler_rate < 0.05:
        rating = "good"
    elif filler_rate < 0.10:
        rating = "okay"
    else:
        rating = "high"
    
    return {
        "rate": filler_rate,
        "percentage": f"{filler_rate*100:.1f}%",
        "rating": rating,
        "score": score,
        "evidence": f"Filler words: {filler_rate*100:.1f}%"
    }

def measure_answer_length(length_s: float) -> dict:
    """
    Score answer length. Ideal: 60-120 seconds.
    Returns: {"seconds": float, "rating": str, "score": 0-1}
    """
    if length_s < 30:
        score = 0.5
        rating = "too short"
    elif length_s < 60:
        gap = 60 - length_s
        score = 0.5 + (gap / 30) * 0.5
        rating = "short"
    elif 60 <= length_s <= 120:
        score = 1.0
        rating = "ideal"
    elif length_s < 180:
        gap = length_s - 120
        score = 0.5 + (gap / 60) * 0.5
        rating = "long"
    else:
        score = 0.5
        rating = "too long"
    
    return {
        "seconds": length_s,
        "rating": rating,
        "score": min(score, 1.0),
        "evidence": f"Answer length: {length_s:.0f}s (ideal: 60-120s)"
    }

def measure_tone_expressiveness(transcript: str) -> dict:
    """
    Measure if tone is expressive (varied) or monotone.
    Look for punctuation variety as a proxy.
    Returns: {"score": 0-1}
    """
    punct_count = sum(1 for c in transcript if c in '!?.')
    variety_score = min(punct_count / max(len(transcript) / 100, 1), 1.0)
    final_score = variety_score * 0.7 + 0.3  # Floor at 0.3
    
    return {
        "punctuation_marks": punct_count,
        "score": final_score,
        "evidence": "Tone shows good variety" if variety_score > 0.5 else "Tone could be more expressive"
    }

# ============================================
# COMMUNICATION FEATURES
# ============================================

def measure_logical_flow(transcript: str) -> dict:
    """
    Measure logical flow with transition words.
    Returns: {"transitions_found": int, "score": 0-1}
    """
    transitions = ["then", "next", "so", "as a result", "meanwhile", "finally", "therefore"]
    count = sum(1 for t in transitions if t in transcript.lower())
    score = min(count / 3.0, 1.0)  # Score peaks at 3+ transitions
    
    return {
        "transitions_found": count,
        "score": score,
        "evidence": f"Found {count} transition phrases"
    }

def measure_clarity(transcript: str) -> dict:
    """
    Measure clarity by average sentence length. Shorter = clearer.
    Returns: {"avg_sentence_length": float, "score": 0-1}
    """
    sentences = [s.strip() for s in transcript.split('.') if s.strip()]
    
    if not sentences:
        return {"avg_sentence_length": 0, "score": 0.5, "evidence": "No sentences found"}
    
    avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
    
    if avg_length < 15:
        score = 1.0
        clarity = "very clear"
    elif avg_length < 20:
        score = 0.8
        clarity = "clear"
    elif avg_length < 30:
        score = 0.6
        clarity = "okay"
    else:
        score = 0.4
        clarity = "complex"
    
    return {
        "avg_sentence_length": avg_length,
        "score": score,
        "clarity": clarity,
        "evidence": f"Average sentence: {avg_length:.0f} words ({clarity})"
    }