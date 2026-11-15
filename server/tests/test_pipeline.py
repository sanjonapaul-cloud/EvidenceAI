"""Question answering, insufficient-evidence behaviour and chat response structure (Members 4 + 5)."""
import pytest

from app.citations.insufficient import INSUFFICIENT_ANSWER
from app.core.errors import ChatInputError
from app.rag.chat_service import ask_question
from app.retrieval.retriever import Retriever
from tests.helpers import FakeLLM

LIMITS_Q = "What are the limitations of the study?"


def _ask(question, llm, registry, embedder, store, metrics, document_ids=()):
    retriever = Retriever(embedder, store, top_k=5, min_score=0.2)
    return ask_question(
        question=question,
        document_ids=list(document_ids),
        registry=registry,
        retriever=retriever,
        llm=llm,
        metrics=metrics,
    )


def test_answered_response_has_correct_structure(loaded, registry, embedder, store, metrics):
    llm = FakeLLM("The study covered a single city and one summer [E1].")
    result = _ask(LIMITS_Q, llm, registry, embedder, store, metrics)
    assert result.status == "answered"
    assert result.answer.startswith("The study covered")
    assert result.citations
    citation = result.citations[0]
    assert set(citation) == {"document_id", "filename", "page", "evidence_id", "excerpt"}
    assert (citation["document_id"], citation["filename"], citation["page"]) == ("doc_001", "cool_roofs.pdf", 3)
    assert citation["evidence_id"] == "E1"
    assert "single city" in citation["excerpt"]


def test_prompt_contains_only_retrieved_evidence_with_ids(loaded, registry, embedder, store, metrics):
    llm = FakeLLM("Answer [E1].")
    _ask(LIMITS_Q, llm, registry, embedder, store, metrics)
    assert "[E1] (file: cool_roofs.pdf, page 3)" in llm.last_prompt
    assert LIMITS_Q in llm.last_prompt


def test_unrelated_question_is_insufficient_and_never_calls_llm(loaded, registry, embedder, store, metrics):
    llm = FakeLLM("Made up answer [E1].")
    result = _ask("Explain quantum chromodynamics gluons", llm, registry, embedder, store, metrics)
    assert result.status == "insufficient_evidence"
    assert result.answer == INSUFFICIENT_ANSWER
    assert result.citations == []
    assert result.note
    assert llm.calls == 0


def test_model_declining_gives_insufficient_evidence(loaded, registry, embedder, store, metrics):
    result = _ask(LIMITS_Q, FakeLLM("INSUFFICIENT_EVIDENCE"), registry, embedder, store, metrics)
    assert result.status == "insufficient_evidence"
    assert result.citations == []


def test_uncited_model_answer_is_not_shown(loaded, registry, embedder, store, metrics):
    result = _ask(LIMITS_Q, FakeLLM("The study proves everything."), registry, embedder, store, metrics)
    assert result.status == "insufficient_evidence"
    assert "proves everything" not in result.answer


def test_fabricated_evidence_ids_are_stripped(loaded, registry, embedder, store, metrics):
    result = _ask(LIMITS_Q, FakeLLM("Real claim [E1]. Fake claim [E42]."), registry, embedder, store, metrics)
    assert result.status == "answered"
    assert "E42" not in result.answer
    assert [c["evidence_id"] for c in result.citations] == ["E1"]


def test_missing_api_key_gives_clearly_labelled_retrieval_only(loaded, registry, embedder, store, metrics):
    llm = FakeLLM(configured=False)
    result = _ask(LIMITS_Q, llm, registry, embedder, store, metrics)
    assert result.status == "retrieval_only"
    assert "not configured" in result.answer
    assert result.citations  # real retrieved evidence
    assert llm.calls == 0


def test_llm_failure_gives_llm_error_with_evidence(loaded, registry, embedder, store, metrics):
    result = _ask(LIMITS_Q, FakeLLM(fail=True), registry, embedder, store, metrics)
    assert result.status == "llm_error"
    assert result.citations


def test_chat_with_no_documents_is_rejected(registry, embedder, store, metrics):
    with pytest.raises(ChatInputError):
        _ask(LIMITS_Q, FakeLLM("x [E1]"), registry, embedder, store, metrics)


def test_chat_with_unknown_document_is_404(loaded, registry, embedder, store, metrics):
    with pytest.raises(ChatInputError) as err:
        _ask(LIMITS_Q, FakeLLM("x [E1]"), registry, embedder, store, metrics, document_ids=["doc_404"])
    assert err.value.status_code == 404


def test_document_selection_limits_search(loaded, settings, registry, embedder, store, metrics, fake_extractor):
    import io

    from app.document_processing.upload_service import handle_upload

    handle_upload(stream=io.BytesIO(b"%PDF-1.4 b"), filename="other.pdf", settings=settings,
                  registry=registry, embedder=embedder, store=store, extractor=fake_extractor)
    result = _ask(LIMITS_Q, FakeLLM("Answer [E1]."), registry, embedder, store, metrics, document_ids=["doc_002"])
    assert result.citations[0]["document_id"] == "doc_002"


def test_metrics_count_each_outcome(loaded, registry, embedder, store, metrics):
    from app.evaluation.summary import build_summary

    summary = build_summary(registry, metrics)
    assert summary["questions_asked"] == 0
    assert summary["evaluation_status"] == "Not yet evaluated"
    assert summary["documents_uploaded"] == 1 and summary["chunks_processed"] > 0

    _ask(LIMITS_Q, FakeLLM("Answer [E1]."), registry, embedder, store, metrics)
    _ask("Explain quantum chromodynamics gluons", FakeLLM("x"), registry, embedder, store, metrics)
    _ask(LIMITS_Q, FakeLLM(configured=False), registry, embedder, store, metrics)
    _ask(LIMITS_Q, FakeLLM(fail=True), registry, embedder, store, metrics)

    summary = build_summary(registry, metrics)
    assert summary["questions_asked"] == 4
    assert summary["answers_returned"] == 1
    assert summary["insufficient_evidence_responses"] == 1
    assert summary["retrieval_only_responses"] == 1
    assert summary["llm_error_responses"] == 1
    assert summary["evaluation_status"] == "Usage counts only"
