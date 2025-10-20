from pydantic import BaseModel
from typing import List, Dict, Optional

# INPUT: What we receive when asking for a score
class ScoreRequest(BaseModel):
    transcript: str  # What the candidate said
    wpm: float  # Words per minute
    filler_rate: float  # Decimal between 0 and 1 (0.05 = 5%)
    answer_length_s: float  # Answer duration in seconds
    jd_keywords: List[str]  # Keywords from job description
    question: str  # The interview question
    candidate_name: str  # Name of the candidate

# OUTPUT: What we send back after scoring
class FeatureScore(BaseModel):
    name: str
    value: float  # 0 to 1
    contribution: float  # How much this helped the score
    evidence: Optional[str] = None  # Why this score

class SubscoreDetail(BaseModel):
    score: float  # 0 to 100
    weight: float  # Its importance
    features: Dict[str, FeatureScore]  # Breakdown of each feature

class ScoreResponse(BaseModel):
    final_score: float  # 0 to 100
    content: SubscoreDetail  # Content score breakdown
    delivery: SubscoreDetail  # Delivery score breakdown
    communication: SubscoreDetail  # Communication score breakdown
    evidence: List[str]  # Bullets explaining why
    next_actions: List[str]  # What to improve
    report_url: Optional[str] = None  # Link to PDF