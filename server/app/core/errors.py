"""Custom exceptions shared across EvidenceAI.

Every exception here carries a *user-safe* message (no stack traces, no secrets)
and an HTTP status code. main.py turns them into JSON error responses, so route
functions do not need their own try/except blocks.
"""
from __future__ import annotations


class EvidenceAIError(Exception):
    """Base class. `message` is safe to show to the end user."""

    status_code = 500

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class UploadValidationError(EvidenceAIError):
    """The uploaded file was rejected before any processing (wrong type, too big, empty)."""

    status_code = 400


class PdfExtractionError(EvidenceAIError):
    """PyMuPDF could not read the PDF (corrupt, password protected, ...)."""

    status_code = 422


class EmbeddingError(EvidenceAIError):
    """The embedding model is missing or failed."""

    status_code = 503


class VectorStoreError(EvidenceAIError):
    """ChromaDB is missing or failed."""

    status_code = 503


class LLMError(EvidenceAIError):
    """The Gemini request failed. The pipeline catches this and returns a clear status."""

    status_code = 502


class ChatInputError(EvidenceAIError):
    """The chat request refers to documents that do not exist or are not searchable."""

    status_code = 400
