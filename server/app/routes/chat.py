
"""POST /api/chat/ask (Member 2)."""

from uuid import uuid4

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_audit_store,
    get_llm,
    get_metrics,
    get_registry,
    get_retriever,
)
from app.core.registry import DocumentRegistry
from app.evaluation.metrics import MetricsStore
from app.audit.store import AuditStore
from app.rag.chat_service import ask_question
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat/ask", response_model=ChatResponse)
def ask(
    request: ChatRequest,
    registry: DocumentRegistry = Depends(get_registry),
    retriever=Depends(get_retriever),
    llm=Depends(get_llm),
    metrics: MetricsStore = Depends(get_metrics),
    audit_store: AuditStore = Depends(get_audit_store),
) -> ChatResponse:
    result = ask_question(
        question=request.question,
        document_ids=request.document_ids,
        registry=registry,
        retriever=retriever,
        llm=llm,
        metrics=metrics,
    )

    # Collect only identifiers and claim statuses, never raw text.
    evidence_ids = {
        citation["evidence_id"]
        for citation in result.citations
        if citation.get("evidence_id")
    }

    claim_statuses = []
    for claim in result.claims:
        claim_statuses.append(claim["status"])
        evidence_ids.update(claim.get("evidence_ids", []))

    audit_store.record_event(
        event_type=f"chat_response_{result.status}",
        request_id=str(uuid4()),
        document_ids=request.document_ids,
        claim_statuses=claim_statuses,
        evidence_ids=sorted(evidence_ids),
    )

    return ChatResponse(
        answer=result.answer,
        status=result.status,
        citations=result.citations,
        note=result.note,
        claims=result.claims,
    )
