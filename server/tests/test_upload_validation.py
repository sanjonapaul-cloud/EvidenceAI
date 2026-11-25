"""Upload validation (Members 2 + 3). These run without a web server."""
import io
from unittest.mock import Mock

import pytest

from app.core.errors import UploadValidationError
from app.document_processing import upload_service
from app.document_processing.upload_service import handle_upload
from app.document_processing.validation import (
    max_bytes,
    validate_filename,
    validate_pdf_header,
)

def _upload(settings, registry, embedder, store, data, name="paper.pdf", extractor=None):
    kwargs = {"extractor": extractor} if extractor else {}
    return handle_upload(
        stream=io.BytesIO(data),
        filename=name,
        settings=settings,
        registry=registry,
        embedder=embedder,
        store=store,
        **kwargs,
    )

def test_filename_must_be_pdf():
    with pytest.raises(UploadValidationError):
        validate_filename("notes.txt")
    with pytest.raises(UploadValidationError):
        validate_filename(None)
    assert validate_filename("Paper.PDF") == "Paper.PDF"

def test_filename_path_parts_are_removed():
    assert validate_filename("../../etc/evil.pdf") == "evil.pdf"
    assert validate_filename("C:\\Users\\me\\paper.pdf") == "paper.pdf"

def test_filename_rejects_empty_pdf_name():
    with pytest.raises(UploadValidationError):
        validate_filename(".pdf")

@pytest.mark.parametrize("filename", ["paper\n.pdf", "paper\x00.pdf", "paper\x7f.pdf"])
def test_filename_rejects_control_characters(filename):
    with pytest.raises(UploadValidationError):
        validate_filename(filename)

def test_filename_rejects_names_over_200_characters():
    with pytest.raises(UploadValidationError):
        validate_filename("a" * 197 + ".pdf")

def test_max_bytes_rejects_non_positive_limits():
    with pytest.raises(UploadValidationError):
        max_bytes(0)

    with pytest.raises(UploadValidationError):
        max_bytes(-1)

def test_max_bytes_converts_megabytes_to_bytes():
    assert max_bytes(1) == 1024 * 1024

def test_header_check_rejects_non_pdf_content():
    with pytest.raises(UploadValidationError):
        validate_pdf_header(b"MZ this is an exe renamed to .pdf")
    validate_pdf_header(b"%PDF-1.7 ...")  # no error

def test_upload_rejects_wrong_extension(settings, registry, embedder, store):
    with pytest.raises(UploadValidationError) as err:
        _upload(settings, registry, embedder, store, b"%PDF-1.4 x", name="paper.docx")
    assert err.value.status_code == 400
    assert registry.list() == []  # nothing registered

def test_upload_rejects_fake_pdf(settings, registry, embedder, store):
    with pytest.raises(UploadValidationError):
        _upload(settings, registry, embedder, store, b"just text, not a pdf")
    assert registry.list() == []

def test_upload_rejects_empty_file(settings, registry, embedder, store):
    with pytest.raises(UploadValidationError) as err:
        _upload(settings, registry, embedder, store, b"")
    assert "empty" in err.value.message.lower()

def test_upload_rejects_too_large_file(settings, registry, embedder, store):
    big = b"%PDF-1.4 " + b"0" * (settings.max_upload_mb * 1024 * 1024 + 10)
    with pytest.raises(UploadValidationError) as err:
        _upload(settings, registry, embedder, store, big)
    assert err.value.status_code == 413
    # Temp file was cleaned up.
    assert not list(settings.uploads_dir.glob("*.tmp"))

def test_upload_success_registers_document_and_chunks(settings, registry, embedder, store, fake_extractor):
    record = _upload(settings, registry, embedder, store, b"%PDF-1.4 ok", extractor=fake_extractor)
    assert record["document_id"] == "doc_001"
    assert record["status"] == "processed"
    assert record["page_count"] == 3
    assert record["chunk_count"] == store.count() > 0
    assert [p["page"] for p in record["pages"]] == [1, 2, 3]
    assert (settings.uploads_dir / "doc_001.pdf").exists()
    assert registry.get("doc_001")["filename"] == "paper.pdf"

def test_document_ids_increase(settings, registry, embedder, store, fake_extractor):
    first = _upload(settings, registry, embedder, store, b"%PDF-1.4 a", extractor=fake_extractor)
    second = _upload(settings, registry, embedder, store, b"%PDF-1.4 b", extractor=fake_extractor)
    assert (first["document_id"], second["document_id"]) == ("doc_001", "doc_002")

def test_scanned_pdf_reports_ocr_not_included(settings, registry, embedder, store):
    from app.document_processing.models import ExtractionResult, PageText

    def scanned(_path):
        return ExtractionResult(page_count=2, pages=[PageText(1, ""), PageText(2, "  ")])

    record = _upload(settings, registry, embedder, store, b"%PDF-1.4 s", extractor=scanned)
    assert record["status"] == "no_text"
    assert "OCR is not included" in record["message"]
    assert store.count() == 0

def test_extraction_failure_marks_document_failed_with_safe_message(settings, registry, embedder, store):
    from app.core.errors import PdfExtractionError

    def broken(_path):
        raise PdfExtractionError("This PDF is password protected and cannot be read.")

    record = _upload(settings, registry, embedder, store, b"%PDF-1.4 p", extractor=broken)
    assert record["status"] == "failed"
    assert "password" in record["message"]

def test_unexpected_error_does_not_leak_details(settings, registry, embedder, store):
    def explode(_path):
        raise RuntimeError("secret internal path /srv/keys")

    record = _upload(settings, registry, embedder, store, b"%PDF-1.4 e", extractor=explode)
    assert record["status"] == "failed"
    assert "secret" not in record["message"]

def test_registry_creation_failure_cleans_temp_file(
    settings, registry, embedder, store
):
    broken_registry = Mock()
    broken_registry.create.side_effect = RuntimeError("registry unavailable")

    with pytest.raises(RuntimeError, match="registry unavailable"):
        _upload(
            settings,
            broken_registry,
            embedder,
            store,
            b"%PDF-1.4 test",
        )

    assert not list(settings.uploads_dir.glob("*.tmp"))


def test_file_move_failure_cleans_temp_file(
    settings, registry, embedder, store, monkeypatch
):
    original_replace = upload_service.Path.replace

    def fail_upload_move(path, target):
        if path.name.startswith("upload_") and path.suffix == ".tmp":
            raise OSError("simulated file move failure")
        return original_replace(path, target)

    monkeypatch.setattr(upload_service.Path, "replace", fail_upload_move)

    with pytest.raises(OSError, match="simulated file move failure"):
        _upload(
            settings,
            registry,
            embedder,
            store,
            b"%PDF-1.4 test",
        )

    assert not list(settings.uploads_dir.glob("*.tmp"))
    record = registry.get("doc_001")
    assert record["status"] == "failed"
    assert record["message"] == (
        "The uploaded file could not be saved. Please try again."
    )


def test_partial_vector_storage_failure_cleans_document_chunks(
    settings, registry, embedder, store, fake_extractor
):
    class PartiallyFailingStore:
        def add_chunks(self, chunks, embeddings):
            # Simulate a storage operation that writes some chunks
            # before encountering an error.
            store.add_chunks(chunks[:1], embeddings[:1])
            raise RuntimeError("simulated partial storage failure")

        def delete_document(self, document_id):
            store.delete_document(document_id)

    record = _upload(
        settings,
        registry,
        embedder,
        PartiallyFailingStore(),
        b"%PDF-1.4 partial",
        extractor=fake_extractor,
    )

    assert record["status"] == "failed"
    assert store.count() == 0
    assert registry.get(record["document_id"])["status"] == "failed"


def test_partial_storage_cleanup_failure_keeps_document_failed(
    settings, registry, embedder, store, fake_extractor
):
    class FailingCleanupStore:
        def add_chunks(self, chunks, embeddings):
            store.add_chunks(chunks[:1], embeddings[:1])
            raise RuntimeError("simulated storage failure")

        def delete_document(self, document_id):
            raise RuntimeError("simulated cleanup failure")

    record = _upload(
        settings,
        registry,
        embedder,
        FailingCleanupStore(),
        b"%PDF-1.4 cleanup",
        extractor=fake_extractor,
    )

    assert record["status"] == "failed"
    assert registry.get(record["document_id"])["status"] == "failed"

    # Cleanup failed, so the partial chunk remains.
    assert store.count() == 1


def test_final_registry_update_failure_cleans_stored_chunks(
    settings, registry, embedder, store, fake_extractor
):
    original_update = registry.update

    def fail_success_update(document_id, **fields):
        if fields.get("status") == "processed":
            raise RuntimeError("simulated registry update failure")
        return original_update(document_id, **fields)

    registry.update = fail_success_update

    record = _upload(
        settings,
        registry,
        embedder,
        store,
        b"%PDF-1.4 registry",
        extractor=fake_extractor,
    )

    # The upload service catches the registry update failure.
    assert record["status"] == "failed"

    # Successfully stored chunks are removed during failure cleanup.
    assert store.count() == 0

    # The registry successfully records the failed status.
    assert registry.get(record["document_id"])["status"] == "failed"


def test_registry_update_failure_leaves_processing_record_but_cleans_chunks(
    settings, registry, embedder, store, fake_extractor
):
    def fail_updates(document_id, **fields):
        raise RuntimeError("simulated registry update failure")

    registry.update = fail_updates

    with pytest.raises(RuntimeError, match="simulated registry update failure"):
        _upload(
            settings,
            registry,
            embedder,
            store,
            b"%PDF-1.4 registry",
            extractor=fake_extractor,
        )

    # Stored chunks are cleaned even though the registry update fails.
    assert store.count() == 0

    # The registry record remains in its original processing state.
    assert registry.get("doc_001")["status"] == "processing"
