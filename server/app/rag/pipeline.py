"""The question-answering pipeline: retrieve -> prompt -> generate -> verify (Members 4 + 5)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from app.citations.evidence import (
    build_evidence,
    evidence_to_citation,
    validate_answer_citations,
)
from app.citations.insufficient import (
    INSUFFICIENT_ANSWER,
    NOTE_MODEL_DECLINED,
    NOTE_NO_RELEVANT_CHUNKS,
    NOTE_UNVERIFIABLE,
    model_declined,
)
from app.core.errors import LLMError
from app.rag.prompt import SYSTEM_INSTRUCTION, build_user_prompt

NOT_CONFIGURED_ANSWER = (
    "The Gemini API key is not configured, so no AI answer was generated. "
    "Below is the most relevant evidence that was retrieved from your documents "
    "(retrieval-only mode)."
)
LLM_ERROR_ANSWER = (
    "The AI service could not be reached or failed, so no answer was generated. "
    "Below is the most relevant evidence that was retrieved from your documents."
)


@dataclass
class AnswerResult:
    answer: str
    status: str  # answered | insufficient_evidence | retrieval_only | llm_error
    citations: list[dict] = field(default_factory=list)
    note: str | None = None


def _insufficient(note: str) -> AnswerResult:
    return AnswerResult(INSUFFICIENT_ANSWER, "insufficient_evidence", [], note)


def answer_question(
    question: str, document_ids: Sequence[str], retriever, llm
) -> AnswerResult:
    # 1. Retrieve. Nothing relevant -> stop here and NEVER call the LLM.
    retrieval = retriever.retrieve(question, document_ids)
    if not retrieval.relevant:
        return _insufficient(NOTE_NO_RELEVANT_CHUNKS)

    evidence = build_evidence(retrieval.relevant)
    all_citations = [evidence_to_citation(e) for e in evidence]

    # 2. No API key -> clearly labelled retrieval-only mode (no fake AI answer).
    if not llm.is_configured:
        return AnswerResult(
            NOT_CONFIGURED_ANSWER,
            "retrieval_only",
            all_citations,
            "Set GEMINI_API_KEY in server/.env and restart the backend to enable AI answers.",
        )

    # 3. Generate a grounded answer.
    try:
        reply = llm.generate(SYSTEM_INSTRUCTION, build_user_prompt(question, evidence))
    except LLMError:
        return AnswerResult(
            LLM_ERROR_ANSWER,
            "llm_error",
            all_citations,
            "Check your API key, model name and internet connection, then try again.",
        )

    # 4. The model itself said the evidence is not enough.
    if model_declined(reply):
        return _insufficient(NOTE_MODEL_DECLINED)

    # 5. Verify citations. An answer with no valid citation cannot be verified.
    check = validate_answer_citations(reply, evidence)
    if not check.cited:
        return _insufficient(NOTE_UNVERIFIABLE)

    return AnswerResult(
        answer=check.clean_answer,
        status="answered",
        citations=[evidence_to_citation(e) for e in check.cited],
        note=None,
    )
