from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.app.services.questions_service import QuestionBank

router = APIRouter()
bank = QuestionBank()

class GapItem(BaseModel):
    skill: str
    status: str  # present | partial | missing

class QuestionsIn(BaseModel):
    gap_map: List[GapItem]

@router.post("/questions")
def questions_endpoint(req: QuestionsIn) -> Dict[str, Any]:
    qs = bank.generate([g.model_dump() for g in req.gap_map])
    return {"questions": qs}
