from pydantic import BaseModel
from typing import List, Tuple, Optional

class SkillSpan(BaseModel):
    name: str
    spans: List[Tuple[int, int]]

class EvidenceItem(BaseModel):
    skill: str
    cv_quote: Optional[str] = ""
    jd_quote: Optional[str] = ""

class SimilarityItem(BaseModel):
    skill: str
    score: float
    cv_sent: str
    jd_sent: str

class GapItem(BaseModel):
    skill: str
    status: str  # present | partial | missing

class SkillsResponse(BaseModel):
    skills_cv: List[SkillSpan]
    skills_jd: List[SkillSpan]
    similarities: List[SimilarityItem]
    gap_map: List[GapItem]
    tips: List[str]
    evidence: List[EvidenceItem]
