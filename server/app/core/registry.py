"""A tiny JSON-file registry that remembers uploaded documents.

ChromaDB stores the searchable chunks; this registry stores the *document-level*
information (filename, status, page info, chunk count). A JSON file keeps the
demo simple and easy to inspect. A real system would use a proper database.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DocumentRegistry:
    def __init__(self, path: Path):
        self._path = Path(path)
        self._lock = threading.Lock()

    # --- low-level file access ----------------------------------------
    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"counter": 0, "documents": {}}
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self._path)  # atomic swap so a crash cannot corrupt the file

    # --- public API -----------------------------------------------------
    def create(self, filename: str, size_bytes: int) -> dict[str, Any]:
        """Register a new document and give it the next ID (doc_001, doc_002, ...)."""
        with self._lock:
            data = self._read()
            data["counter"] += 1
            doc_id = f"doc_{data['counter']:03d}"
            record = {
                "document_id": doc_id,
                "filename": filename,
                "size_bytes": size_bytes,
                "status": "processing",
                "message": "Processing started.",
                "page_count": 0,
                "pages_with_text": 0,
                "chunk_count": 0,
                "pages": [],
                "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            data["documents"][doc_id] = record
            self._write(data)
            return dict(record)

    def update(self, document_id: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            record = data["documents"][document_id]
            record.update(fields)
            self._write(data)
            return dict(record)

    def get(self, document_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read()["documents"].get(document_id)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            docs = list(self._read()["documents"].values())
        return sorted(docs, key=lambda d: d["document_id"])

    def totals(self) -> dict[str, int]:
        docs = self.list()
        processed = [d for d in docs if d["status"] == "processed"]
        return {
            "documents_uploaded": len(docs),
            "documents_processed": len(processed),
            "chunks_processed": sum(d.get("chunk_count", 0) for d in processed),
        }
