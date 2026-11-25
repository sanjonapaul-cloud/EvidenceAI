"""Tests for vector-store document ID discovery."""

from app.document_processing.models import Chunk
from app.retrieval.vector_store import ChromaVectorStore


def test_empty_store_returns_no_document_ids(store):
    assert store.list_document_ids() == set()


def test_store_lists_document_ids(loaded, store):
    assert store.list_document_ids() == {"doc_001"}


def test_chroma_empty_store_returns_no_document_ids(tmp_path):
    vector_store = ChromaVectorStore(tmp_path / "chroma")

    assert vector_store.list_document_ids() == set()


def test_chroma_lists_unique_document_ids(tmp_path):
    vector_store = ChromaVectorStore(tmp_path / "chroma")

    chunks = [
        Chunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            filename="first.pdf",
            page=1,
            chunk_index=0,
            text="First document chunk.",
            char_start=0,
            char_end=21,
        ),
        Chunk(
            chunk_id="chunk_002",
            document_id="doc_001",
            filename="first.pdf",
            page=1,
            chunk_index=1,
            text="Second document chunk.",
            char_start=22,
            char_end=44,
        ),
        Chunk(
            chunk_id="chunk_003",
            document_id="doc_002",
            filename="second.pdf",
            page=1,
            chunk_index=0,
            text="Another document chunk.",
            char_start=0,
            char_end=23,
        ),
    ]

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    vector_store.add_chunks(chunks, embeddings)

    assert vector_store.list_document_ids() == {"doc_001", "doc_002"}