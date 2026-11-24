"""HTTP-level tests through FastAPI's TestClient (Members 2 + 6).

Skipped automatically when fastapi / httpx are not installed. Heavy components (embedding model,
ChromaDB, Gemini) are replaced with the fakes from tests/helpers.py.
"""
import io
import os
import tempfile
import sqlite3

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
from app.audit.store import AuditStore


@pytest.fixture
def client(tmp_path):
    settings = make_settings(tmp_path, audit_api_key="test-audit-secret")
    registry = DocumentRegistry(settings.registry_path)
    metrics = MetricsStore(settings.metrics_path)

    audit_store = AuditStore(settings.audit_db_path)
    audit_store.initialize()

    embedder, store = HashingEmbedder(), InMemoryVectorStore()
    llm = FakeLLM([
    "The study covered a single city [E1].",
    '{"status": "supported", "explanation": "The cited passage explicitly states that the study covered a single city."}'
    ])

    app = create_app()
    app.dependency_overrides.update(
        {
            deps.get_settings: lambda: settings,
            deps.get_registry: lambda: registry,
            deps.get_metrics: lambda: metrics,
            deps.get_audit_store: lambda: audit_store,
            deps.get_embedder: lambda: embedder,
            deps.get_vector_store: lambda: store,
            deps.get_llm: lambda: llm,
        }
    )
    test_client = TestClient(app, headers={"X-Audit-API-Key": "test-audit-secret"})
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
    assert set(data["citations"][0]) == {
        "document_id",
        "filename",
        "page",
        "evidence_id",
        "excerpt",
        "chunk_id",
        "chunk_index",
        "char_start",
        "char_end",
    }

    assert data["citations"][0]["chunk_id"]
    assert data["citations"][0]["chunk_index"] is not None
    assert data["citations"][0]["char_start"] is not None
    assert data["citations"][0]["char_end"] > data["citations"][0]["char_start"]
    assert isinstance(data["claims"], list)

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



def test_chat_request_creates_persistent_audit_event(client, monkeypatch):
    _fake_extractor_patch(monkeypatch)

    upload = _upload(client)
    assert upload.status_code == 200

    response = client.post(
        "/api/chat/ask",
        json={
            "question": "What are the limitations of the study?",
            "document_ids": ["doc_001"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "answered"

    audit_path = client.app.dependency_overrides[
        deps.get_audit_store
    ]().db_path

    connection = sqlite3.connect(audit_path)
    try:
        rows = connection.execute(
            """
            SELECT event_type, document_ids,
                   claim_status_counts, evidence_ids
            FROM audit_events
            """
        ).fetchall()
    finally:
        connection.close()

    assert len(rows) == 1

    event_type, document_ids, claim_status_counts, evidence_ids = rows[0]

    import json

    assert event_type == "chat_response_answered"
    assert json.loads(document_ids) == ["doc_001"]
    assert json.loads(claim_status_counts) == {"supported": 1}
    assert json.loads(evidence_ids) == ["E1"]


def test_audit_events_endpoint_returns_empty_list(client):
    response = client.get("/api/audit/events")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["events"] == []


def test_audit_events_endpoint_returns_persisted_events(client):
    audit_store = client.app.dependency_overrides[
        deps.get_audit_store
    ]()

    audit_store.record_event(
        event_type="answer_generated",
        request_id="request-001",
        document_ids=["doc-001"],
        claim_statuses=["supported", "insufficient"],
        evidence_ids=["E1", "E2"],
    )

    response = client.get("/api/audit/events")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1

    event = body["events"][0]
    assert event["request_id"] == "request-001"
    assert event["event_type"] == "answer_generated"
    assert event["document_ids"] == ["doc-001"]
    assert event["claim_status_counts"] == {
        "supported": 1,
        "insufficient": 1,
    }
    assert event["evidence_ids"] == ["E1", "E2"]

    assert "question" not in event
    assert "answer" not in event
    assert "excerpt" not in event


def test_audit_events_endpoint_supports_filtering_and_pagination(client):
    audit_store = client.app.dependency_overrides[
        deps.get_audit_store
    ]()

    audit_store.record_event(event_type="answer_generated")
    audit_store.record_event(event_type="retrieval_completed")
    audit_store.record_event(event_type="answer_generated")

    response = client.get(
        "/api/audit/events",
        params={
            "event_type": "answer_generated",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["events"]) == 1
    assert body["events"][0]["event_type"] == "answer_generated"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_audit_events_endpoint_rejects_invalid_parameters(
    client, params
):
    response = client.get("/api/audit/events", params=params)

    assert response.status_code == 422


def test_audit_events_endpoint_returns_empty_list(client):
    response = client.get("/api/audit/events")

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 0
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["events"] == []


def test_audit_events_endpoint_returns_persisted_events(client):
    audit_store = client.app.dependency_overrides[
        deps.get_audit_store
    ]()

    audit_store.record_event(
        event_type="answer_generated",
        request_id="request-001",
        document_ids=["doc-001"],
        claim_statuses=["supported", "insufficient"],
        evidence_ids=["E1", "E2"],
    )

    response = client.get("/api/audit/events")

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1

    event = body["events"][0]
    assert event["request_id"] == "request-001"
    assert event["event_type"] == "answer_generated"
    assert event["document_ids"] == ["doc-001"]
    assert event["claim_status_counts"] == {
        "supported": 1,
        "insufficient": 1,
    }
    assert event["evidence_ids"] == ["E1", "E2"]

    assert "question" not in event
    assert "answer" not in event
    assert "excerpt" not in event


def test_audit_events_endpoint_supports_filtering_and_pagination(client):
    audit_store = client.app.dependency_overrides[
        deps.get_audit_store
    ]()

    audit_store.record_event(event_type="answer_generated")
    audit_store.record_event(event_type="retrieval_completed")
    audit_store.record_event(event_type="answer_generated")

    response = client.get(
        "/api/audit/events",
        params={
            "event_type": "answer_generated",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["events"]) == 1
    assert body["events"][0]["event_type"] == "answer_generated"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_audit_events_endpoint_rejects_invalid_parameters(
    client, params
):
    response = client.get("/api/audit/events", params=params)

    assert response.status_code == 422


def test_audit_events_requires_valid_api_key(client):
    unauthenticated_client = TestClient(client.app)

    missing_key_response = unauthenticated_client.get("/api/audit/events")
    assert missing_key_response.status_code == 401

    wrong_key_response = unauthenticated_client.get(
        "/api/audit/events",
        headers={"X-Audit-API-Key": "wrong-test-key"},
    )
    assert wrong_key_response.status_code == 401

    valid_key_response = client.get("/api/audit/events")
    assert valid_key_response.status_code == 200


def test_audit_events_fails_closed_when_server_key_is_not_configured(
    client, tmp_path
):
    client.app.dependency_overrides[deps.get_settings] = (
        lambda: make_settings(tmp_path, audit_api_key="")
    )

    unauthenticated_client = TestClient(client.app)
    response = unauthenticated_client.get("/api/audit/events")

    assert response.status_code == 503
    assert response.json()["detail"] == "Audit access is not configured."
