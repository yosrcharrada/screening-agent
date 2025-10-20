from fastapi import APIRouter, HTTPException
from typing import Dict
import uuid
from datetime import datetime

from ..models.score_models import ScoreRequest, ScoreResponse, SubscoreDetail, FeatureScore
from ..services.score_calculator import calculate_score
from ..services.pdf_generator import save_pdf_report

router = APIRouter(prefix="/api", tags=["scoring"])


@router.post("/score", response_model=ScoreResponse)
async def score_interview_answer(request: ScoreRequest) -> ScoreResponse:
    """
    Score an interview answer and return detailed breakdown with XAI evidence.
    
    This endpoint takes transcript + metrics and returns:
    - Final score (0-100)
    - Content/Delivery/Communication subscores
    - Per-feature contributions (XAI)
    - Evidence bullets explaining the score
    - Next action items for improvement
    """
    
    try:
        # Calculate the score using our scoring engine
        score_result = calculate_score(
            transcript=request.transcript,
            wpm=request.wpm,
            filler_rate=request.filler_rate,
            answer_length_s=request.answer_length_s,
            jd_keywords=request.jd_keywords,
            question=request.question
        )
        
        # Generate session ID for this scoring
        session_id = str(uuid.uuid4())
        
        # Generate PDF report
        pdf_path = save_pdf_report(
            score_data=score_result,
            candidate_name=request.candidate_name,
            question=request.question,
            session_id=session_id
        )
        
        # Build the response according to our data model
        response = ScoreResponse(
            final_score=score_result['final_score'],
            content=SubscoreDetail(
                score=score_result['content']['score'],
                weight=score_result['content']['weight'],
                features={
                    name: FeatureScore(
                        name=name,
                        value=data['score'],
                        contribution=data['contribution'],
                        evidence=data['evidence']
                    )
                    for name, data in score_result['content']['features'].items()
                }
            ),
            delivery=SubscoreDetail(
                score=score_result['delivery']['score'],
                weight=score_result['delivery']['weight'],
                features={
                    name: FeatureScore(
                        name=name,
                        value=data['score'],
                        contribution=data['contribution'],
                        evidence=data['evidence']
                    )
                    for name, data in score_result['delivery']['features'].items()
                }
            ),
            communication=SubscoreDetail(
                score=score_result['communication']['score'],
                weight=score_result['communication']['weight'],
                features={
                    name: FeatureScore(
                        name=name,
                        value=data['score'],
                        contribution=data['contribution'],
                        evidence=data['evidence']
                    )
                    for name, data in score_result['communication']['features'].items()
                }
            ),
            evidence=score_result['evidence'],
            next_actions=score_result['next_actions'],
            report_url=f"/reports/{session_id}"  # URL to download PDF
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating score: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "scoring",
        "timestamp": datetime.now().isoformat()
    }