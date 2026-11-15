"""GET /api/evaluation/summary (Member 5)."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_metrics, get_registry
from app.core.registry import DocumentRegistry
from app.evaluation.metrics import MetricsStore
from app.evaluation.summary import build_summary
from app.schemas import EvaluationSummary

router = APIRouter()


@router.get("/evaluation/summary", response_model=EvaluationSummary)
def evaluation_summary(
    registry: DocumentRegistry = Depends(get_registry),
    metrics: MetricsStore = Depends(get_metrics),
) -> EvaluationSummary:
    return EvaluationSummary(**build_summary(registry, metrics))
