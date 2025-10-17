from fastapi import APIRouter
from app.models.schemas import TranscribeRequest, TranscribeResponse, HintItem, STARStructure

router = APIRouter()

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    # Stub implementation with mock transcription
    return TranscribeResponse(
        text_partial="I led a project to implement a new feature where we had to integrate with multiple APIs. The situation was challenging because of tight deadlines...",
        wpm=145.5,
        filler_rate=0.02,
        length_s=45.2,
        hints=[
            HintItem(reason="Speaking too fast", at_s=12.5),
            HintItem(reason="Use more specific examples", at_s=28.7)
        ],
        star=STARStructure(
            S="Tight deadlines for API integration project",
            T="Lead the implementation of new feature", 
            A="Coordinated team, created integration plan, implemented fallbacks",
            R="Successfully delivered on time with 99.9% reliability"
        )
    )