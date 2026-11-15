"""Validates a chat request against known documents, then runs the RAG pipeline (Members 2 + 4)."""
from __future__ import annotations

from typing import Sequence

from app.core.errors import ChatInputError
from app.core.registry import DocumentRegistry
from app.evaluation.metrics import MetricsStore
from app.rag.pipeline import AnswerResult, answer_question


def ask_question(
    *,
    question: str,
    document_ids: Sequence[str],
    registry: DocumentRegistry,
    retriever,
    llm,
    metrics: MetricsStore,
) -> AnswerResult:
    docs = {d["document_id"]: d for d in registry.list()}

    if document_ids:
        unknown = [d for d in document_ids if d not in docs]
        if unknown:
            raise ChatInputError("One or more selected documents do not exist.", status_code=404)
        selected = [d for d in document_ids if docs[d]["status"] == "processed"]
        if not selected:
            raise ChatInputError(
                "None of the selected documents has searchable text. "
                "Check the document status on the dashboard."
            )
    else:
        selected = [d for d, rec in docs.items() if rec["status"] == "processed"]
        if not selected:
            raise ChatInputError("There are no searchable documents yet. Upload a PDF first.")

    result = answer_question(question, selected, retriever, llm)
    metrics.record(result.status)  # only completed questions are counted
    return result
