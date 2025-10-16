from pydantic import BaseModel
from typing import List

class QuestionItem(BaseModel):
    id: str
    text: str
    difficulty: str
    rationale: str

class QuestionsResponse(BaseModel):
    questions: List[QuestionItem]
