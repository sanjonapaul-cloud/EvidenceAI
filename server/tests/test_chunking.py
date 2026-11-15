"""PDF text cleaning, chunking and chunk metadata preservation (Member 3)."""
import pytest

from app.document_processing.chunker import chunk_pages, split_text
from app.document_processing.cleaner import clean_text
from app.document_processing.models import PageText


def test_clean_text_joins_hyphenated_words_and_collapses_whitespace():
    assert clean_text("evalu-\nation   of\n\nmodels") == "evaluation of models"


def test_clean_text_handles_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_split_text_overlaps_and_covers_all_text():
    text = " ".join(f"word{i}" for i in range(200))
    pieces = split_text(text, chunk_size=200, overlap=40)
    assert len(pieces) > 3
    assert all(len(p) <= 200 for _, _, p in pieces)
    # Overlap: each chunk begins before the previous chunk ended.
    for (s1, e1, _), (s2, _e2, _) in zip(pieces, pieces[1:]):
        assert s2 < e1
        assert s2 > s1
    # Every word appears in at least one chunk (nothing lost).
    joined = " ".join(p for _, _, p in pieces)
    assert all(f"word{i}" in joined for i in range(200))


def test_split_text_makes_progress_on_one_very_long_word():
    pieces = split_text("x" * 1000, chunk_size=100, overlap=20)
    assert len(pieces) >= 10  # terminates and covers the text


def test_split_text_rejects_bad_parameters():
    with pytest.raises(ValueError):
        split_text("hello", chunk_size=100, overlap=100)


def test_chunk_text_is_verbatim_slice_of_its_own_page_with_exact_offsets():
    page_texts = {
        1: clean_text("Alpha section. " + "Reflective coatings reduce heat. " * 40),
        2: clean_text("Bravo section. " + "Sensors record temperature often. " * 40),
    }
    pages = [PageText(n, t) for n, t in page_texts.items()]
    chunks = chunk_pages("doc_001", "t.pdf", pages, chunk_size=250, overlap=50)
    assert {c.page for c in chunks} == {1, 2}
    for c in chunks:
        assert page_texts[c.page][c.char_start : c.char_end] == c.text
        other_page = 2 if c.page == 1 else 1
        assert ("Alpha" in c.text) is False or c.page == 1
        assert ("Bravo" in c.text) is False or c.page == 2
        assert c.text not in page_texts[other_page]


def test_chunks_keep_document_and_page_metadata():
    pages = [
        PageText(1, "First page sentence one. " * 30),
        PageText(2, ""),  # an empty page produces no chunks
        PageText(3, "Third page sentence about limitations. " * 30),
    ]
    chunks = chunk_pages("doc_007", "paper.pdf", pages, chunk_size=300, overlap=50)
    assert chunks
    assert {c.page for c in chunks} == {1, 3}  # page 2 had no text, numbers are not shifted
    for c in chunks:
        assert c.document_id == "doc_007"
        assert c.filename == "paper.pdf"
        assert c.chunk_id.startswith(f"doc_007_p{c.page}_c")
        meta = c.to_metadata()
        assert meta["page"] == c.page and meta["document_id"] == "doc_007"
    # Chunk text really comes from its own page (no mixing between pages).
    assert all("limitations" in c.text for c in chunks if c.page == 3)
    assert all("limitations" not in c.text for c in chunks if c.page == 1)
    # Chunk IDs are unique.
    assert len({c.chunk_id for c in chunks}) == len(chunks)
