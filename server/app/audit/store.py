
"""Persistent, privacy-minimized audit event storage."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class AuditStore:
    """Store audit metadata without retaining raw questions or evidence text."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """Create the database and its tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.db_path, timeout=10)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=10000")

            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id TEXT PRIMARY KEY,
                        request_id TEXT,
                        event_type TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        document_ids TEXT NOT NULL,
                        claim_status_counts TEXT NOT NULL,
                        evidence_ids TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
                    ON audit_events(created_at)
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_audit_events_request_id
                    ON audit_events(request_id)
                    """
                )
        finally:
            connection.close()

    def record_event(
        self,
        *,
        event_type: str,
        request_id: str | None = None,
        document_ids: list[str] | None = None,
        claim_statuses: list[str] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> str:
        """Persist one event and return its generated ID.

        Store identifiers and claim-status counts only. Do not pass raw
        questions, answers, claim text, prompts, or evidence excerpts.
        """
        if not event_type.strip():
            raise ValueError("event_type must not be empty")

        status_counts = dict(Counter(claim_statuses or []))
        event_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        connection = sqlite3.connect(self.db_path, timeout=10)
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            with connection:
                connection.execute(
                    """
                    INSERT INTO audit_events (
                        event_id,
                        request_id,
                        event_type,
                        created_at,
                        document_ids,
                        claim_status_counts,
                        evidence_ids
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        request_id,
                        event_type,
                        created_at,
                        json.dumps(document_ids or []),
                        json.dumps(status_counts),
                        json.dumps(evidence_ids or []),
                    ),
                )
        finally:
            connection.close()

        return event_id
