"""Upload validation rules (Members 2 + 3). Pure functions, easy to test."""
from __future__ import annotations

import os

from app.core.errors import UploadValidationError

PDF_MAGIC = b"%PDF-"

def validate_filename(filename: str | None) -> str:
    """Return a safe display filename, or raise UploadValidationError."""
    if not filename:
        raise UploadValidationError("No file name was provided.")

    # Drop directory parts to prevent path traversal.
    safe = os.path.basename(filename.replace("\\", "/")).strip()

    if not safe or safe.lower() == ".pdf":
        raise UploadValidationError("A valid PDF file name is required.")

    # Reject control characters, including newlines and null bytes.
    if any(ord(char) < 32 or ord(char) == 127 for char in safe):
        raise UploadValidationError("The file name contains invalid characters.")

    if not safe.lower().endswith(".pdf"):
        raise UploadValidationError("Only PDF files (.pdf) are supported.")

    if len(safe) > 200:
        raise UploadValidationError("The file name is too long.")

    return safe

def validate_pdf_header(first_block: bytes) -> None:
    """A PDF signature must appear within the first 1024 bytes."""
    if PDF_MAGIC not in first_block[:1024]:
        raise UploadValidationError("This file does not look like a valid PDF.")

def max_bytes(max_upload_mb: int) -> int:
    """Convert the configured upload limit to bytes."""
    if max_upload_mb <= 0:
        raise UploadValidationError(
            "The maximum upload size must be greater than zero."
        )
    return max_upload_mb * 1024 * 1024
