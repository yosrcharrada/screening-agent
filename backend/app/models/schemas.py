from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Health Response
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

# Parse Request/Response
class ParseRequest(BaseModel):
    cv_text: str
    jd_text: str

class ParseResponse(BaseModel):
    cv_text: str
    jd_text: str

# Skills Request/Response
class SkillsRequest(BaseModel):
    cv_text: str
    jd_text: str

class SkillsResponse(BaseModel):
    skills_cv: List[str]
    skills_jd: List[str]
    similarities: List[Dict[str, Any]]
    gap_map: Dict[str, Any]
    tips: List[str]
    evidence: List[Dict[str, Any]]

# Questions Request/Response
class QuestionItem(BaseModel):
    id: str
    text: str
    difficulty: str
    rationale: str

class QuestionsRequest(BaseModel):
    jd_text: str
    count: int = 5

class QuestionsResponse(BaseModel):
    questions: List[QuestionItem]

# Transcribe Request/Response
class HintItem(BaseModel):
    reason: str
    at_s: float

class STARStructure(BaseModel):
    S: Optional[str] = None
    T: Optional[str] = None  
    A: Optional[str] = None
    R: Optional[str] = None

class TranscribeRequest(BaseModel):
    audio_data: str  # base64 encoded audio for now
    session_id: str

class TranscribeResponse(BaseModel):
    text_partial: str
    wpm: float
    filler_rate: float
    length_s: float
    hints: List[HintItem]
    star: STARStructure

# Score Request/Response
class ContentFeatures(BaseModel):
    relevance: float
    depth: float
    structure: float
    examples: float

class DeliveryFeatures(BaseModel):
    pace: float
    clarity: float
    confidence: float
    enthusiasm: float

class CommunicationFeatures(BaseModel):
    grammar: float
    vocabulary: float
    conciseness: float
    engagement: float

class ScoreRequest(BaseModel):
    session_id: str
    transcript: str
    jd_text: str

class ScoreResponse(BaseModel):
    final: float
    content: Dict[str, Any]
    delivery: Dict[str, Any]
    communication: Dict[str, Any]
    next_actions: List[str]

# Report Request/Response
class ReportRequest(BaseModel):
    session_id: str

class ReportResponse(BaseModel):
    pdf_url: str