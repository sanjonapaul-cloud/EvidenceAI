"""HTTP-level tests through FastAPI's TestClient (Members 2 + 6).

Skipped automatically when fastapi / httpx are not installed. Heavy components (embedding model,
ChromaDB, Gemini) are replaced with the fakes from tests/helpers.py.
"""
import io
import os
import tempfile

import pytest

# Keep the app from creating its data folders inside the real project while testing.
os.environ.setdefault("EVIDENCEAI_DATA_DIR", tempfile.mkdtemp(prefix="evidenceai_test_"))

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.core import dependencies as deps  # noqa: E402
from app.core.registry import DocumentRegistry  # noqa: E402
from app.evaluation.metrics import MetricsStore  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.helpers import SAMPLE_PAGES, FakeLLM, HashingEmbedder, InMemoryVectorStore, make_settings  # noqa: E402


@pytest.fixture
def client(tmp_path):
    settings = make_settings(tmp_path)
    registry = DocumentRegistry(settings.registry_path)
    metrics = MetricsStore(settings.metrics_path)
    embedder, store = HashingEmbedder(), InMemoryVectorStore()
    llm = FakeLLM("The study covered a single city [E1].")

    app = create_app()
    app.dependency_overrides.update(
        {
            deps.get_settings: lambda: settings,
            deps.get_registry: lambda: registry,
            deps.get_metrics: lambda: metrics,
            deps.get_embedder: lambda: embedder,
            deps.get_vector_store: lambda: store,
            deps.get_llm: lambda: llm,
        }
    )
    test_client = TestClient(app)
    test_client.llm = llm
    return test_client


def _fake_extractor_patch(monkeypatch):
    from app.document_processing import upload_service
    from app.document_processing.models import ExtractionResult, PageText

    def fake(_path):
        pages = [PageText(n, t) for n, t in SAMPLE_PAGES.items()]
        return ExtractionResult(page_count=len(pages), pages=pages)

    monkeypatch.setattr(upload_service, "extract_pdf", fake)


def _upload(client, data=b"%PDF-1.4 fake", name="cool_roofs.pdf"):
    return client.post("/api/documents/upload", files={"file": (name, io.BytesIO(data), "application/pdf")})


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["llm_configured"] is False
    assert "api_key" not in str(body).lower()


def test_upload_rejects_non_pdf(client):
    response = _upload(client, b"hello", "notes.txt")
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_rejects_fake_pdf_content(client):
    assert _upload(client, b"not a pdf at all").status_code == 400


def test_upload_requires_file_field(client):
    assert client.post("/api/documents/upload").status_code == 422


def test_upload_list_chat_and_evaluation_flow(client, monkeypatch):
    _fake_extractor_patch(monkeypatch)

    upload = _upload(client)
    assert upload.status_code == 200
    body = upload.json()
    assert body["document_id"] == "doc_001" and body["status"] == "processed"
    assert body["processing_summary"]["page_count"] == 3

    listing = client.get("/api/documents").json()["documents"]
    assert [d["document_id"] for d in listing] == ["doc_001"]

    ask = client.post(
        "/api/chat/ask",
        json={"question": "What are the limitations of the study?", "document_ids": ["doc_001"], "session_id": "s1"},
    )
    assert ask.status_code == 200
    data = ask.json()
    assert data["status"] == "answered"
    assert set(data["citations"][0]) == {"document_id", "filename", "page", "evidence_id", "excerpt"}

    insufficient = client.post(
        "/api/chat/ask", json={"question": "Explain quantum chromodynamics gluons", "document_ids": ["doc_001"]}
    ).json()
    assert insufficient["status"] == "insufficient_evidence"
    assert insufficient["citations"] == []
    assert insufficient["answer"].startswith("Insufficient evidence in the uploaded documents")

    summary = client.get("/api/evaluation/summary").json()
    assert summary["questions_asked"] == 2
    assert summary["answers_returned"] == 1
    assert summary["insufficient_evidence_responses"] == 1


def test_chat_validation_errors(client):
    assert client.post("/api/chat/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/api/chat/ask", json={}).status_code == 422
    no_docs = client.post("/api/chat/ask", json={"question": "What is this about?"})
    assert no_docs.status_code == 400
    assert "Upload a PDF" in no_docs.json()["detail"]


def test_evaluation_summary_starts_at_zero(client):
    body = client.get("/api/evaluation/summary").json()
    assert body["questions_asked"] == 0
    assert body["evaluation_status"] == "Not yet evaluated"
