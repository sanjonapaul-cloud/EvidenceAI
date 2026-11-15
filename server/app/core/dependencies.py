"""Shared objects for the API routes (created once, on first use).

Routes ask for these with FastAPI's `Depends(...)`. Tests replace them with fakes via
`app.dependency_overrides`. Heavy things (embedding model, ChromaDB) are created lazily so
the server starts instantly and still starts when optional packages are missing.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings, load_settings
from app.core.registry import DocumentRegistry
from app.embeddings.embedder import SentenceTransformerEmbedder
from app.evaluation.metrics import MetricsStore
from app.rag.gemini_client import GeminiLLM
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import ChromaVectorStore


@lru_cache
def get_settings() -> Settings:
    return load_settings()


@lru_cache
def get_registry() -> DocumentRegistry:
    return DocumentRegistry(get_settings().registry_path)


@lru_cache
def get_metrics() -> MetricsStore:
    return MetricsStore(get_settings().metrics_path)


@lru_cache
def get_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(get_settings().embedding_model)


@lru_cache
def get_vector_store() -> ChromaVectorStore:
    return ChromaVectorStore(get_settings().chroma_dir)


@lru_cache
def get_llm() -> GeminiLLM:
    return GeminiLLM(get_settings())


def get_retriever(
    settings: Settings = Depends(get_settings),
    embedder=Depends(get_embedder),
    store=Depends(get_vector_store),
) -> Retriever:
    # Not cached: it is a cheap object, and it picks up whatever embedder/store is injected.
    return Retriever(embedder, store, top_k=settings.top_k, min_score=settings.min_relevance_score)
