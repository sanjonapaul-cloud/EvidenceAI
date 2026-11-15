"""Handles one uploaded file: validate -> save -> register -> process (Members 2 + 3).

This is plain Python (no FastAPI types), so it can be unit-tested without a web server.
The route in routes/documents.py is just a thin wrapper around `handle_upload`.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Callable

from app.core.config import Settings
from app.core.errors import EvidenceAIError, UploadValidationError
from app.core.registry import DocumentRegistry
from app.document_processing.extractor import extract_pdf
from app.document_processing.processing import process_document
from app.document_processing.validation import max_bytes, validate_filename, validate_pdf_header

logger = logging.getLogger("evidenceai.upload")
READ_BLOCK = 1024 * 1024  # 1 MB


def _save_stream_to_temp(stream: BinaryIO, settings: Settings) -> tuple[Path, int]:
    """Copy the upload to a temp file while enforcing the size limit."""
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    limit = max_bytes(settings.max_upload_mb)
    temp_path = settings.uploads_dir / f"upload_{uuid.uuid4().hex}.tmp"
    size = 0
    try:
        with open(temp_path, "wb") as out:
            first = True
            while True:
                block = stream.read(READ_BLOCK)
                if not block:
                    break
                if first:
                    validate_pdf_header(block)
                    first = False
                size += len(block)
                if size > limit:
                    raise UploadValidationError(
                        f"File is too large. The maximum size is {settings.max_upload_mb} MB.",
                        status_code=413,
                    )
                out.write(block)
        if size == 0:
            raise UploadValidationError("The uploaded file is empty.")
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path, size


def handle_upload(
    *,
    stream: BinaryIO,
    filename: str | None,
    settings: Settings,
    registry: DocumentRegistry,
    embedder,
    store,
    extractor: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Validate and process an uploaded PDF. Returns the document's registry record.

    Raises UploadValidationError for rejected files (HTTP 400/413). Problems that
    happen *during processing* do not raise: they are stored on the document as
    status "failed" with a safe message, so the dashboard can show them.
    """
    extractor = extractor or extract_pdf  # resolved at call time (tests can swap it)
    safe_name = validate_filename(filename)
    temp_path, size = _save_stream_to_temp(stream, settings)

    record = registry.create(safe_name, size)
    document_id = record["document_id"]
    pdf_path = settings.uploads_dir / f"{document_id}.pdf"  # our own name: no path tricks
    temp_path.replace(pdf_path)

    try:
        result = process_document(
            document_id=document_id,
            filename=safe_name,
            pdf_path=pdf_path,
            settings=settings,
            embedder=embedder,
            store=store,
            extractor=extractor,
        )
        return registry.update(
            document_id,
            status=result.status,
            message=result.message,
            page_count=result.page_count,
            pages_with_text=result.pages_with_text,
            chunk_count=result.chunk_count,
            pages=result.pages,
        )
    except Exception as exc:
        # Log the technical details on the server only; show the user a safe message.
        logger.exception("Processing failed for %s", document_id)
        message = (
            exc.message
            if isinstance(exc, EvidenceAIError)
            else "Processing failed unexpectedly. Check the server logs for details."
        )
        try:
            store.delete_document(document_id)  # do not leave half-indexed chunks behind
        except Exception:  # pragma: no cover - best effort cleanup
            logger.exception("Cleanup failed for %s", document_id)
        return registry.update(document_id, status="failed", message=message)
