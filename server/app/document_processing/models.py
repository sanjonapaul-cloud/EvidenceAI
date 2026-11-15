"""Small data containers used by the PDF-processing code (Member 3)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    """Text of ONE PDF page. `page_number` is 1-based, like the page numbers a reader sees."""

    page_number: int
    text: str


@dataclass
class ExtractionResult:
    page_count: int
    pages: list[PageText] = field(default_factory=list)


@dataclass(frozen=True)
class Chunk:
    """A piece of text from ONE page, with everything needed to cite it later."""

    chunk_id: str
    document_id: str
    filename: str
    page: int
    chunk_index: int
    text: str
    char_start: int
    char_end: int

    def to_metadata(self) -> dict:
        """Metadata stored next to the chunk in ChromaDB (values must be simple types)."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "page": self.page,
            "chunk_index": self.chunk_index,
            "char_start": self.char_start,
            "char_end": self.char_end,
        }
