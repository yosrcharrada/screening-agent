from fastapi import APIRouter
from app.models.schemas import SkillsRequest, SkillsResponse

router = APIRouter()

@router.post("/skills", response_model=SkillsResponse)
async def analyze_skills(request: SkillsRequest):
    # Stub implementation with mock data
    return SkillsResponse(
        skills_cv=["Python", "FastAPI", "SQL", "Machine Learning"],
        skills_jd=["Python", "FastAPI", "Docker", "AWS", "Kubernetes"],
        similarities=[
            {"skill": "Python", "match_score": 0.95},
            {"skill": "FastAPI", "match_score": 0.88}
        ],
        gap_map={
            "missing_skills": ["Docker", "AWS", "Kubernetes"],
            "strong_skills": ["Python", "Machine Learning"]
        },
        tips=[
            "Consider learning Docker for containerization",
            "AWS cloud skills are in high demand",
            "Practice system design questions"
        ],
        evidence=[
            {"type": "skill_match", "details": "Python experience matches requirement"},
            {"type": "skill_gap", "details": "Docker experience needed"}
        ]
    )