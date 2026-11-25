"""Pydantic models = the API contract (request and response shapes).

Owner: Member 2 (Backend). The frontend (client/src/services/api.js) and
docs/api_contracts.md must stay in sync with this file.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str
    app: str
    llm_configured: bool
    gemini_model: str
    embedding_model: str


class PageInfo(BaseModel):
    page: int
    char_count: int


class DocumentOut(BaseModel):
    document_id: str
    filename: str
    status: Literal["processing", "processed", "no_text", "failed"]
    message: str
    size_bytes: int
    page_count: int
    pages_with_text: int
    chunk_count: int
    uploaded_at: str
    pages: List[PageInfo] = []


class DocumentListResponse(BaseModel):
    documents: List[DocumentOut]


class ProcessingSummary(BaseModel):
    page_count: int
    pages_with_text: int
    chunk_count: int
    size_bytes: int


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: Literal["processing", "processed", "no_text", "failed"]
    message: str
    processing_summary: ProcessingSummary


class ChatRequest(BaseModel):
    question: str
    # Empty list (or omitted) means "search all processed documents".
    document_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None

    @field_validator("question")
    @classmethod
    def question_must_be_reasonable(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Question is too short.")
        if len(value) > 2000:
            raise ValueError("Question is too long (max 2000 characters).")
        return value


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int
    evidence_id: str
    excerpt: str
    chunk_id: str
    chunk_index: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ClaimAssessment(BaseModel):
    claim: str
    evidence_ids: List[str]
    status: Literal[
        "supported",
        "partially_supported",
        "contradicted",
        "insufficient",
    ]
    explanation: str
    sources: List[Citation] = Field(default_factory=list)

class TrustReport(BaseModel):
    total_claims: int
    supported: int
    partially_supported: int
    contradicted: int
    insufficient: int
    unsupported: int
    coverage_percent: Optional[float] = None
    gaps: List[dict] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "insufficient_evidence", "retrieval_only", "llm_error"]
    citations: List[Citation]
    note: Optional[str] = None
    claims: List[ClaimAssessment] = Field(default_factory=list)
    trust_report: Optional[TrustReport] = None


class EvaluationSummary(BaseModel):
    documents_uploaded: int
    documents_processed: int
    chunks_processed: int
    questions_asked: int
    answers_returned: int
    insufficient_evidence_responses: int
    retrieval_only_responses: int
    llm_error_responses: int
    evaluation_status: str
    note: str
