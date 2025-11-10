import logging
from typing import List, Dict
from .question_xai import question_xai_judge

logger = logging.getLogger(__name__)

def attach_xai_to_questions(cv_text: str, jd_text: str, questions: List[Dict]) -> List[Dict]:
    out = []
    for q in questions:
        try:
            xai = question_xai_judge.explain_question(q, cv_text, jd_text)
            q = dict(q); q["xai"] = xai
            out.append(q)
        except Exception as e:
            logger.error(f"XAI attach failed: {e}")
            q = dict(q)
            q["xai"] = {
                "rationale": q.get("rationale", "This question explores relevant skills."),
                "alignment_score": 0.0,
                "cv_evidence": [],
                "jd_evidence": [],
                "hallucination_flags": ["xai_attach_failed"]
            }
            out.append(q)
    return out