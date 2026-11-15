"""The processing pipeline for one document: extract -> clean -> chunk -> embed -> store.

The embedder, vector store and extractor are passed in (dependency injection).
That keeps this file easy to test with small fake components.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.core.config import Settings
from app.document_processing.chunker import chunk_pages
from app.document_processing.cleaner import clean_text
from app.document_processing.extractor import extract_pdf
from app.document_processing.models import ExtractionResult, PageText

EMBED_BATCH_SIZE = 32
MIN_PAGE_TEXT_CHARS = 20  # a page with fewer characters is treated as "no text"

OCR_MESSAGE = (
    "No extractable text was found. This looks like a scanned or image-only PDF. "
    "OCR is not included in this initial version."
)


@dataclass
class ProcessingResult:
    status: str  # "processed" or "no_text"
    message: str
    page_count: int
    pages_with_text: int
    chunk_count: int
    pages: list[dict] = field(default_factory=list)


def process_document(
    *,
    document_id: str,
    filename: str,
    pdf_path: Path,
    settings: Settings,
    embedder,
    store,
    extractor: Callable[[Path], ExtractionResult] = extract_pdf,
) -> ProcessingResult:
    extraction = extractor(pdf_path)

    cleaned_pages = [PageText(p.page_number, clean_text(p.text)) for p in extraction.pages]
    page_info = [{"page": p.page_number, "char_count": len(p.text)} for p in cleaned_pages]
    pages_with_text = sum(1 for p in cleaned_pages if len(p.text) >= MIN_PAGE_TEXT_CHARS)

    chunks = chunk_pages(
        document_id, filename, cleaned_pages, settings.chunk_size, settings.chunk_overlap
    )
    if not chunks:
        return ProcessingResult(
            status="no_text",
            message=OCR_MESSAGE,
            page_count=extraction.page_count,
            pages_with_text=0,
            chunk_count=0,
            pages=page_info,
        )

    embeddings: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        embeddings.extend(embedder.embed_documents([c.text for c in batch]))

    store.add_chunks(chunks, embeddings)

    message = f"Processed {extraction.page_count} page(s) into {len(chunks)} searchable chunk(s)."
    empty_pages = extraction.page_count - pages_with_text
    if empty_pages > 0:
        message += (
            f" {empty_pages} page(s) had no extractable text (possibly scanned images; "
            "OCR is not included in this initial version)."
        )
    return ProcessingResult(
        status="processed",
        message=message,
        page_count=extraction.page_count,
        pages_with_text=pages_with_text,
        chunk_count=len(chunks),
        pages=page_info,
    )
