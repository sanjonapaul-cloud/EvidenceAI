"""Upload validation rules (Members 2 + 3). Pure functions, easy to test."""
from __future__ import annotations

import os

from app.core.errors import UploadValidationError

PDF_MAGIC = b"%PDF-"


def validate_filename(filename: str | None) -> str:
    """Return a safe display filename, or raise UploadValidationError."""
    if not filename:
        raise UploadValidationError("No file name was provided.")
    # Drop any directory part (blocks names like ../../evil.pdf), keep only the base name.
    safe = os.path.basename(filename.replace("\\", "/")).strip()
    if not safe.lower().endswith(".pdf"):
        raise UploadValidationError("Only PDF files (.pdf) are supported.")
    if len(safe) > 200:
        raise UploadValidationError("The file name is too long.")
    return safe


def validate_pdf_header(first_block: bytes) -> None:
    """A real PDF has '%PDF-' near the start. This catches renamed non-PDF files."""
    if PDF_MAGIC not in first_block[:1024]:
        raise UploadValidationError("This file does not look like a valid PDF.")


def max_bytes(max_upload_mb: int) -> int:
    return max_upload_mb * 1024 * 1024
