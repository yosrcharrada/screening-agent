from fastapi import APIRouter
from app.models.schemas import ScoreRequest, ScoreResponse

router = APIRouter()

@router.post("/score", response_model=ScoreResponse)
async def score_interview(request: ScoreRequest):
    # Stub implementation with mock scores
    return ScoreResponse(
        final=7.8,
        content={
            "score": 8.2,
            "features": {
                "relevance": 8.5,
                "depth": 7.9,
                "structure": 8.0,
                "examples": 8.5
            }
        },
        delivery={
            "score": 7.4,
            "features": {
                "pace": 7.0,
                "clarity": 8.0,
                "confidence": 7.5,
                "enthusiasm": 7.0
            }
        },
        communication={
            "score": 7.8,
            "features": {
                "grammar": 8.5,
                "vocabulary": 7.5,
                "conciseness": 7.0,
                "engagement": 8.0
            }
        },
        next_actions=[
            "Practice speaking at a slower pace",
            "Include more quantitative results in examples", 
            "Work on reducing filler words"
        ]
    )