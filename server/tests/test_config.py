from app.core.config import load_settings


def test_max_pdf_pages_defaults_to_500(monkeypatch):
    monkeypatch.delenv("MAX_PDF_PAGES", raising=False)

    assert load_settings().max_pdf_pages == 500


def test_max_pdf_pages_accepts_custom_positive_value(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "120")

    assert load_settings().max_pdf_pages == 120


def test_max_pdf_pages_rejects_zero(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "0")

    assert load_settings().max_pdf_pages == 500


def test_max_pdf_pages_rejects_negative_value(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "-10")

    assert load_settings().max_pdf_pages == 500


def test_max_pdf_pages_rejects_non_integer_value(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "invalid")

    assert load_settings().max_pdf_pages == 500
