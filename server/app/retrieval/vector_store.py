"""ChromaDB-backed vector store (Member 4).

ChromaDB stores each chunk's text, its embedding and its metadata (document ID,
filename, page number). It saves to disk, so documents survive a server restart.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from app.core.errors import VectorStoreError
from app.document_processing.models import Chunk
from app.retrieval.base import RetrievedChunk

logger = logging.getLogger("evidenceai.vectorstore")
COLLECTION_NAME = "evidenceai_chunks"


class ChromaVectorStore:
    def __init__(self, persist_dir: Path):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError as exc:
            raise VectorStoreError(
                "chromadb is not installed. Run: pip install -r requirements.txt"
            ) from exc
        try:
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # "cosine" distance: score = 1 - distance is an easy-to-read similarity.
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
        except Exception as exc:
            logger.exception("Could not open ChromaDB")
            raise VectorStoreError("The vector database could not be opened.") from exc

    def add_chunks(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunk and embedding counts do not match.")
        if not chunks:
            return
        try:
            self._collection.upsert(
                ids=[c.chunk_id for c in chunks],
                embeddings=[list(e) for e in embeddings],
                documents=[c.text for c in chunks],
                metadatas=[c.to_metadata() for c in chunks],
            )
        except Exception as exc:
            logger.exception("ChromaDB write failed")
            raise VectorStoreError("Saving chunks to the vector database failed.") from exc

    def query(
        self, embedding: Sequence[float], top_k: int, document_ids: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        try:
            total = self._collection.count()
            if total == 0:
                return []
            kwargs = {
                "query_embeddings": [list(embedding)],
                "n_results": min(top_k, total),
                "include": ["documents", "metadatas", "distances"],
            }
            if document_ids:
                kwargs["where"] = {"document_id": {"$in": list(document_ids)}}
            result = self._collection.query(**kwargs)
        except Exception as exc:
            logger.exception("ChromaDB query failed")
            raise VectorStoreError("Searching the vector database failed.") from exc

        hits: list[RetrievedChunk] = []
        ids = result["ids"][0]
        for i, chunk_id in enumerate(ids):
            meta = result["metadatas"][0][i]
            hits.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=meta["document_id"],
                    filename=meta["filename"],
                    page=int(meta["page"]),
                    text=result["documents"][0][i],
                    score=1.0 - float(result["distances"][0][i]),
                    chunk_index=int(meta["chunk_index"]),
                    char_start=int(meta["char_start"]),
                    char_end=int(meta["char_end"]),
                )
            )
        return hits

    def delete_document(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as exc:
            logger.exception("ChromaDB delete failed")
            raise VectorStoreError("Removing document chunks failed.") from exc

    def count(self) -> int:
        return self._collection.count()

    def list_document_ids(self) -> set[str]:
        """Return unique document IDs represented in the vector collection."""
        try:
            result = self._collection.get(include=["metadatas"])
            metadatas = result.get("metadatas") or []
            return {
                metadata["document_id"]
                for metadata in metadatas
                if metadata and metadata.get("document_id")
            }
        except Exception as exc:
            logger.exception("ChromaDB document ID listing failed")
            raise VectorStoreError(
                "Listing document IDs from the vector database failed."
            ) from exc
