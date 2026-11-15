"""Shared pytest fixtures."""
import pytest

from app.core.registry import DocumentRegistry
from app.document_processing.models import ExtractionResult, PageText
from app.evaluation.metrics import MetricsStore
from tests.helpers import SAMPLE_PAGES, HashingEmbedder, InMemoryVectorStore, make_settings


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture
def registry(tmp_path):
    return DocumentRegistry(tmp_path / "documents.json")


@pytest.fixture
def metrics(tmp_path):
    return MetricsStore(tmp_path / "metrics.json")


@pytest.fixture
def embedder():
    return HashingEmbedder()


@pytest.fixture
def store():
    return InMemoryVectorStore()


@pytest.fixture
def fake_extractor():
    """Pretends to read a PDF and returns the three SAMPLE_PAGES."""

    def _extract(_path):
        pages = [PageText(n, t) for n, t in SAMPLE_PAGES.items()]
        return ExtractionResult(page_count=len(pages), pages=pages)

    return _extract


@pytest.fixture
def loaded(settings, registry, embedder, store, fake_extractor):
    """A registry + store that already contains one processed document (doc_001)."""
    import io

    from app.document_processing.upload_service import handle_upload

    record = handle_upload(
        stream=io.BytesIO(b"%PDF-1.4 fake pdf bytes"),
        filename="cool_roofs.pdf",
        settings=settings,
        registry=registry,
        embedder=embedder,
        store=store,
        extractor=fake_extractor,
    )
    assert record["status"] == "processed"
    return record
