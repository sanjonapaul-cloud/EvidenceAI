"""Real PDF extraction with PyMuPDF (Member 3). Skipped automatically if PyMuPDF is not installed."""
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from app.document_processing.chunker import chunk_pages  # noqa: E402
from app.document_processing.cleaner import clean_text  # noqa: E402
from app.document_processing.extractor import extract_pdf  # noqa: E402
from app.document_processing.models import PageText  # noqa: E402
from app.core.errors import PdfExtractionError  # noqa: E402

SAMPLE_PDF = Path(__file__).resolve().parents[2] / "sample_data" / "evidenceai_sample_paper.pdf"


def _make_pdf(path, page_texts):
    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(72, 72, 520, 760), text, fontsize=11)
    doc.save(str(path))
    doc.close()


def test_pages_are_extracted_in_order_with_one_based_numbers(tmp_path):
    pdf = tmp_path / "t.pdf"
    _make_pdf(pdf, ["Alpha page one text.", "Bravo page two text.", "Charlie page three text."])
    result = extract_pdf(pdf)
    assert result.page_count == 3
    assert [p.page_number for p in result.pages] == [1, 2, 3]
    assert "Alpha" in result.pages[0].text and "Charlie" in result.pages[2].text


def test_page_numbers_survive_chunking(tmp_path):
    pdf = tmp_path / "t.pdf"
    _make_pdf(pdf, ["Alpha " * 80, "Bravo " * 80])
    pages = [PageText(p.page_number, clean_text(p.text)) for p in extract_pdf(pdf).pages]
    chunks = chunk_pages("doc_001", "t.pdf", pages, 200, 40)
    assert all(("Alpha" in c.text) == (c.page == 1) for c in chunks)
    assert all(("Bravo" in c.text) == (c.page == 2) for c in chunks)


def test_blank_page_pdf_extracts_empty_text(tmp_path):
    pdf = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf))
    doc.close()
    assert clean_text(extract_pdf(pdf).pages[0].text) == ""


def test_corrupt_pdf_raises_safe_error(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.4 this is not really a pdf")
    with pytest.raises(PdfExtractionError):
        extract_pdf(bad)


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="sample PDF not generated")
def test_bundled_sample_pdf_has_expected_pages():
    result = extract_pdf(SAMPLE_PDF)
    assert result.page_count == 3
    assert "Limitations" in result.pages[2].text


def test_pdf_at_page_limit_is_accepted(tmp_path):
    pdf = tmp_path / "at_limit.pdf"
    _make_pdf(pdf, ["Page one.", "Page two.", "Page three."])

    result = extract_pdf(pdf, max_pages=3)

    assert result.page_count == 3
    assert len(result.pages) == 3


def test_pdf_over_page_limit_is_rejected(tmp_path):
    pdf = tmp_path / "over_limit.pdf"
    _make_pdf(pdf, ["Page one.", "Page two.", "Page three."])

    with pytest.raises(PdfExtractionError) as exc:
        extract_pdf(pdf, max_pages=2)

    assert exc.value.status_code == 413
    assert "maximum supported is 2" in str(exc.value).lower()
