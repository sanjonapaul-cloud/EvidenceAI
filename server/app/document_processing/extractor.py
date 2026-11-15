"""PDF text extraction with PyMuPDF, one page at a time (Member 3).

Extracting page by page is what lets us cite "page 7" later: the page number
travels with the text through chunking, embedding, storage and retrieval.
"""
from __future__ import annotations

from pathlib import Path

from app.core.errors import PdfExtractionError
from app.document_processing.models import ExtractionResult, PageText


def extract_pdf(pdf_path: Path) -> ExtractionResult:
    try:
        import fitz  # PyMuPDF's import name
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise PdfExtractionError(
            "PyMuPDF is not installed on the server. Run: pip install -r requirements.txt",
            status_code=503,
        ) from exc

    try:
        document = fitz.open(str(pdf_path))
    except Exception as exc:
        raise PdfExtractionError("This file could not be opened as a PDF (it may be corrupt).") from exc

    try:
        if document.needs_pass:
            raise PdfExtractionError("This PDF is password protected and cannot be read.")
        if document.page_count == 0:
            raise PdfExtractionError("This PDF has no pages.")

        pages = []
        for index in range(document.page_count):
            page = document.load_page(index)
            # Page numbers are 1-based so they match what a person sees in a PDF viewer.
            pages.append(PageText(page_number=index + 1, text=page.get_text("text")))
        return ExtractionResult(page_count=document.page_count, pages=pages)
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError("Text could not be extracted from this PDF.") from exc
    finally:
        document.close()
