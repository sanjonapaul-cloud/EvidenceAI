"""GET /api/health (Member 2)."""
from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.core.dependencies import get_settings
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    # Reports whether a Gemini key exists (True/False only). The key itself is never returned.
    return HealthResponse(
        status="ok",
        app="EvidenceAI",
        llm_configured=settings.llm_configured,
        gemini_model=settings.gemini_model,
        embedding_model=settings.embedding_model,
    )
