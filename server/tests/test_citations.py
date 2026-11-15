"""Evidence IDs and citation validation (Member 5)."""
from app.citations.evidence import (
    build_evidence,
    evidence_to_citation,
    extract_cited_ids,
    make_excerpt,
    validate_answer_citations,
)
from app.citations.insufficient import model_declined
from app.retrieval.base import RetrievedChunk


def _hits():
    return [
        RetrievedChunk("c1", "doc_001", "a.pdf", 3, "Limitations: single city, one summer. " * 5, 0.9),
        RetrievedChunk("c2", "doc_002", "b.pdf", 8, "Methods used paired buildings.", 0.6),
    ]


def test_evidence_ids_are_sequential_and_keep_metadata():
    evidence = build_evidence(_hits())
    assert [e.evidence_id for e in evidence] == ["E1", "E2"]
    assert (evidence[1].document_id, evidence[1].filename, evidence[1].page) == ("doc_002", "b.pdf", 8)


def test_citation_has_all_required_fields():
    citation = evidence_to_citation(build_evidence(_hits())[0])
    assert set(citation) == {"document_id", "filename", "page", "evidence_id", "excerpt"}
    assert citation["page"] == 3 and citation["evidence_id"] == "E1"


def test_excerpt_is_real_source_text_and_truncated():
    long_text = "alpha beta gamma delta " * 50
    excerpt = make_excerpt(long_text, max_chars=100)
    assert excerpt.endswith("…")
    assert long_text.startswith(excerpt[:-1])
    assert len(excerpt) <= 101
    assert make_excerpt("short text") == "short text"


def test_extract_cited_ids_handles_formats():
    assert extract_cited_ids("A [E1]. B [E2, E3] and [e1][E4].") == ["E1", "E2", "E3", "E4"]
    assert extract_cited_ids("no citations here") == []


def test_invalid_ids_are_removed_and_never_become_citations():
    evidence = build_evidence(_hits())
    check = validate_answer_citations("Fact one [E1]. Invented fact [E9]. Mixed [E2, E7].", evidence)
    assert check.invalid_ids == ["E9", "E7"]
    assert "E9" not in check.clean_answer and "E7" not in check.clean_answer
    assert [e.evidence_id for e in check.cited] == ["E1", "E2"]


def test_answer_without_markers_has_no_cited_evidence():
    check = validate_answer_citations("A confident claim with no citation.", build_evidence(_hits()))
    assert check.cited == []


def test_model_declined_detection():
    assert model_declined("INSUFFICIENT_EVIDENCE")
    assert model_declined("insufficient evidence")
    assert not model_declined("The study found a result [E1].")
