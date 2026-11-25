"""Shared types for retrieval (Member 4)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from app.document_processing.models import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page: int
    text: str
    score: float  # similarity, higher = more relevant (1.0 = identical meaning)
    chunk_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None


class VectorStore(Protocol):
    """What the rest of the app needs from a vector database."""

    def add_chunks(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None: ...

    def query(
        self, embedding: Sequence[float], top_k: int, document_ids: Sequence[str] | None = None
    ) -> list[RetrievedChunk]: ...

    def delete_document(self, document_id: str) -> None: ...

    def count(self) -> int: ...

    def list_document_ids(self) -> set[str]: ...
