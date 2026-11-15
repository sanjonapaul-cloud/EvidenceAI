"""Turn a question into the most relevant chunks (Member 4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from app.retrieval.base import RetrievedChunk


@dataclass
class RetrievalResult:
    relevant: list[RetrievedChunk] = field(default_factory=list)  # passed the score threshold
    best_score: float | None = None  # best score seen, even if below threshold (for debugging)


class Retriever:
    def __init__(self, embedder, store, top_k: int = 5, min_score: float = 0.30):
        self.embedder = embedder
        self.store = store
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(self, question: str, document_ids: Sequence[str] | None = None) -> RetrievalResult:
        query_vector = self.embedder.embed_query(question)
        hits = self.store.query(query_vector, self.top_k, document_ids)
        if not hits:
            return RetrievalResult()
        hits = sorted(hits, key=lambda h: h.score, reverse=True)
        # Weak matches are dropped: they are the main source of unsupported answers.
        relevant = [h for h in hits if h.score >= self.min_score]
        return RetrievalResult(relevant=relevant, best_score=hits[0].score)
