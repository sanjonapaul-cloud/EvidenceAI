"""Builds the /api/evaluation/summary response (Member 5)."""
from __future__ import annotations

from app.core.registry import DocumentRegistry
from app.evaluation.metrics import MetricsStore

NOTE = (
    "These are usage counts only. No accuracy, faithfulness or relevance scores have been "
    "computed in this initial version."
)


def build_summary(registry: DocumentRegistry, metrics: MetricsStore) -> dict:
    totals = registry.totals()
    counts = metrics.snapshot()
    asked = counts["questions_asked"]
    return {
        **totals,
        "questions_asked": asked,
        "answers_returned": counts["answered"],
        "insufficient_evidence_responses": counts["insufficient_evidence"],
        "retrieval_only_responses": counts["retrieval_only"],
        "llm_error_responses": counts["llm_error"],
        "evaluation_status": "Not yet evaluated" if asked == 0 else "Usage counts only",
        "note": NOTE,
    }
