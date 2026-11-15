"""Retrieval with fake embeddings (Member 4). Tests the plumbing, not semantic quality."""
from app.retrieval.retriever import Retriever


def _retriever(embedder, store, min_score=0.2):
    return Retriever(embedder, store, top_k=5, min_score=min_score)


def test_relevant_question_returns_chunk_from_correct_page(loaded, embedder, store):
    result = _retriever(embedder, store).retrieve("What are the limitations of the study?")
    assert result.relevant
    top = result.relevant[0]
    assert top.page == 3
    assert top.document_id == "doc_001"
    assert top.filename == "cool_roofs.pdf"
    assert "Limitations" in top.text


def test_results_are_sorted_by_score(loaded, embedder, store):
    result = _retriever(embedder, store, min_score=0.0).retrieve("sensors recorded air temperature")
    scores = [h.score for h in result.relevant]
    assert scores == sorted(scores, reverse=True)
    assert result.relevant[0].page == 2


def test_unrelated_question_returns_nothing_relevant(loaded, embedder, store):
    result = _retriever(embedder, store).retrieve("Explain quantum chromodynamics gluons")
    assert result.relevant == []


def test_document_filter_is_respected(loaded, embedder, store):
    result = _retriever(embedder, store, min_score=0.0).retrieve("limitations", ["doc_999"])
    assert result.relevant == []


def test_empty_store_returns_empty_result(embedder, store):
    result = _retriever(embedder, store).retrieve("anything at all")
    assert result.relevant == [] and result.best_score is None
