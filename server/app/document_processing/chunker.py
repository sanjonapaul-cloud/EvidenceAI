"""Split page text into overlapping chunks (Member 3).

Key design rule: a chunk NEVER spans two pages. Chunking each page separately
means every chunk has exactly one, correct page number.
"""
from __future__ import annotations

import re

from app.document_processing.models import Chunk, PageText

MIN_CHUNK_CHARS = 20  # ignore tiny fragments such as a lone page number


def _find_break(text: str, start: int, end: int) -> int:
    """Pick a nicer place to cut than exactly `end`: a sentence end, else a space."""
    lower = start + int((end - start) * 0.6)  # only look in the last 40% of the window
    window = text[lower:end]
    best = -1
    for match in re.finditer(r"[.!?]\s", window):
        best = match.end()
    if best != -1:
        return lower + best
    space = window.rfind(" ")
    if space != -1:
        return lower + space + 1
    return end  # no good place found (very long word): hard cut


def split_text(text: str, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    """Return (start, end, piece) tuples. Consecutive pieces overlap by ~`overlap` chars."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be > 0 and 0 <= overlap < chunk_size")

    text = text.strip()
    length = len(text)
    pieces: list[tuple[int, int, str]] = []
    start = 0
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            end = _find_break(text, start, end)
        raw = text[start:end]
        piece = raw.strip()
        if piece:
            offset = len(raw) - len(raw.lstrip())
            pieces.append((start + offset, start + offset + len(piece), piece))
        if end >= length:
            break

        next_start = end - overlap
        if next_start <= start:  # always make progress
            next_start = end
        # Start the next chunk at the beginning of a word, not in the middle of one.
        while start < next_start < end and not text[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return pieces


def chunk_pages(
    document_id: str,
    filename: str,
    pages: list[PageText],
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[Chunk]:
    """Chunk every page and attach document/page metadata to each chunk."""
    chunks: list[Chunk] = []
    index = 0
    for page in pages:
        for start, end, piece in split_text(page.text, chunk_size, overlap):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}_p{page.page_number}_c{index}",
                    document_id=document_id,
                    filename=filename,
                    page=page.page_number,
                    chunk_index=index,
                    text=piece,
                    char_start=start,
                    char_end=end,
                )
            )
            index += 1
    return chunks
