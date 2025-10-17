from fastapi import APIRouter
from app.models.schemas import ParseRequest, ParseResponse

router = APIRouter()

@router.post("/parse", response_model=ParseResponse)
async def parse_documents(request: ParseRequest):
    # Stub implementation - just echo back the input
    return ParseResponse(
        cv_text=request.cv_text,
        jd_text=request.jd_text
    )