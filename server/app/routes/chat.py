"""POST /api/chat/ask (Member 2)."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_llm, get_metrics, get_registry, get_retriever
from app.core.registry import DocumentRegistry
from app.evaluation.metrics import MetricsStore
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
) -> ChatResponse:
    result = ask_question(
        question=request.question,
        document_ids=request.document_ids,
        registry=registry,
        retriever=retriever,
        llm=llm,
        metrics=metrics,
    )
    return ChatResponse(
        answer=result.answer,
        status=result.status,
        citations=result.citations,
        note=result.note,
    )
