
"""Persistent audit-store tests."""

import json
import sqlite3

import pytest

from app.audit.store import AuditStore


def test_initialize_creates_database_and_table(tmp_path):
    db_path = tmp_path / "audit.db"
    audit = AuditStore(db_path)

    audit.initialize()

    assert db_path.exists()

    connection = sqlite3.connect(db_path)
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    connection.close()

    assert ("audit_events",) in tables


def test_initialize_is_safe_to_call_multiple_times(tmp_path):
    audit = AuditStore(tmp_path / "audit.db")

    audit.initialize()
    audit.initialize()

    assert audit.db_path.exists()


def test_record_event_persists_metadata(tmp_path):
    db_path = tmp_path / "audit.db"
    audit = AuditStore(db_path)
    audit.initialize()

    event_id = audit.record_event(
        event_type="answer_generated",
        request_id="request-001",
        document_ids=["doc-001"],
        claim_statuses=["supported", "supported", "insufficient"],
        evidence_ids=["E1", "E2"],
    )

    connection = sqlite3.connect(db_path)
    row = connection.execute(
        """
        SELECT event_id, request_id, event_type, document_ids,
               claim_status_counts, evidence_ids
        FROM audit_events
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()
    connection.close()

    assert row is not None
    assert row[0] == event_id
    assert row[1] == "request-001"
    assert row[2] == "answer_generated"
    assert json.loads(row[3]) == ["doc-001"]
    assert json.loads(row[4]) == {
        "supported": 2,
        "insufficient": 1,
    }
    assert json.loads(row[5]) == ["E1", "E2"]


def test_record_event_generates_unique_ids(tmp_path):
    audit = AuditStore(tmp_path / "audit.db")
    audit.initialize()

    first_id = audit.record_event(event_type="first")
    second_id = audit.record_event(event_type="second")

    assert first_id != second_id


def test_record_event_supports_optional_fields(tmp_path):
    audit = AuditStore(tmp_path / "audit.db")
    audit.initialize()

    event_id = audit.record_event(event_type="retrieval_completed")

    connection = sqlite3.connect(audit.db_path)
    row = connection.execute(
        """
        SELECT document_ids, claim_status_counts, evidence_ids
        FROM audit_events WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()
    connection.close()

    assert json.loads(row[0]) == []
    assert json.loads(row[1]) == {}
    assert json.loads(row[2]) == []


def test_record_event_rejects_empty_event_type(tmp_path):
    audit = AuditStore(tmp_path / "audit.db")
    audit.initialize()

    with pytest.raises(ValueError, match="event_type"):
        audit.record_event(event_type="   ")


def test_audit_store_does_not_store_raw_claim_or_evidence_text(tmp_path):
    db_path = tmp_path / "audit.db"
    audit = AuditStore(db_path)
    audit.initialize()

    audit.record_event(
        event_type="answer_generated",
        document_ids=["doc-001"],
        claim_statuses=["supported"],
        evidence_ids=["E1"],
    )

    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT * FROM audit_events"
    ).fetchall()
    connection.close()

    stored_data = repr(rows)

    assert "raw private claim text" not in stored_data
    assert "raw evidence excerpt" not in stored_data
