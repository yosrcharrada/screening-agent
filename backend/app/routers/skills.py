from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict
from backend.app.services.skills_service import SkillsEngine

router = APIRouter()
engine = SkillsEngine()

class SkillsIn(BaseModel):
    cv_text: str
    jd_text: str

@router.post("/skills")
def skills_endpoint(req: SkillsIn) -> Dict[str, Any]:
    return engine.payload(req.cv_text, req.jd_text)
