"""Simple usage counters saved in a JSON file (Member 5).

These are COUNTS of what happened. They are not accuracy scores.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

COUNTER_NAMES = (
    "questions_asked",
    "answered",
    "insufficient_evidence",
    "retrieval_only",
    "llm_error",
)


class MetricsStore:
    def __init__(self, path: Path):
        self._path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, int]:
        data = {name: 0 for name in COUNTER_NAMES}
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                data.update(json.load(f))
        return data

    def record(self, status: str) -> None:
        """Count one completed question with the given answer status."""
        with self._lock:
            data = self._read()
            data["questions_asked"] += 1
            if status in data:
                data[status] += 1
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self._path)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return self._read()
