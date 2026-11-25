"""Tests for the persistent document registry."""

from app.core.registry import DocumentRegistry


def test_create_document_assigns_sequential_ids(tmp_path):
    registry = DocumentRegistry(tmp_path / "documents.json")

    first = registry.create("first.pdf", 100)
    second = registry.create("second.pdf", 200)

    assert first["document_id"] == "doc_001"
    assert second["document_id"] == "doc_002"
    assert first["status"] == "processing"
    assert second["status"] == "processing"


def test_registry_persists_documents_after_recreation(tmp_path):
    path = tmp_path / "documents.json"

    registry = DocumentRegistry(path)
    created = registry.create("report.pdf", 500)

    # Simulate reopening the registry.
    reopened_registry = DocumentRegistry(path)

    record = reopened_registry.get(created["document_id"])

    assert record is not None
    assert record["filename"] == "report.pdf"
    assert record["size_bytes"] == 500
    assert record["status"] == "processing"


def test_update_changes_document_status(tmp_path):
    registry = DocumentRegistry(tmp_path / "documents.json")
    created = registry.create("report.pdf", 500)

    updated = registry.update(
        created["document_id"],
        status="processed",
        chunk_count=4,
    )

    assert updated["status"] == "processed"
    assert updated["chunk_count"] == 4


def test_list_returns_documents_in_id_order(tmp_path):
    registry = DocumentRegistry(tmp_path / "documents.json")

    registry.create("first.pdf", 100)
    registry.create("second.pdf", 200)

    records = registry.list()

    assert [record["document_id"] for record in records] == [
        "doc_001",
        "doc_002",
    ]


def test_totals_counts_only_processed_documents(tmp_path):
    registry = DocumentRegistry(tmp_path / "documents.json")

    first = registry.create("first.pdf", 100)
    registry.create("second.pdf", 200)

    registry.update(
        first["document_id"],
        status="processed",
        chunk_count=3,
    )

    assert registry.totals() == {
        "documents_uploaded": 2,
        "documents_processed": 1,
        "chunks_processed": 3,
    }