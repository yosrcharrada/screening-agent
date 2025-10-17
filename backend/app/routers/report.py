from fastapi import APIRouter
from app.models.schemas import ReportRequest, ReportResponse

router = APIRouter()

@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    # Stub implementation with mock PDF URL
    return ReportResponse(
        pdf_url="https://example.com/reports/session_12345.pdf"
    )