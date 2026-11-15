"""Application settings.

All configuration comes from environment variables. For local development put
them in `server/.env` (copy `server/.env.example`). Nothing secret is ever
hardcoded in the source code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# server/ directory (this file is server/app/core/config.py)
SERVER_DIR = Path(__file__).resolve().parents[2]
load_dotenv(SERVER_DIR / ".env")

# Values that mean "the key was not really set".
PLACEHOLDER_KEYS = {"", "your_gemini_api_key_here", "changeme"}


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    embedding_model: str
    data_dir: Path
    max_upload_mb: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_relevance_score: float
    cors_origins: list[str]

    # --- derived paths -------------------------------------------------
    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def registry_path(self) -> Path:
        return self.data_dir / "documents.json"

    @property
    def metrics_path(self) -> Path:
        return self.data_dir / "metrics.json"

    @property
    def llm_configured(self) -> bool:
        return self.gemini_api_key.strip() not in PLACEHOLDER_KEYS

    def ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """Build a Settings object from the current environment."""
    data_dir = Path(os.getenv("EVIDENCEAI_DATA_DIR", "data"))
    if not data_dir.is_absolute():
        data_dir = SERVER_DIR / data_dir

    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        data_dir=data_dir,
        max_upload_mb=_get_int("MAX_UPLOAD_MB", 20),
        chunk_size=_get_int("CHUNK_SIZE", 800),
        chunk_overlap=_get_int("CHUNK_OVERLAP", 150),
        top_k=_get_int("TOP_K", 5),
        min_relevance_score=_get_float("MIN_RELEVANCE_SCORE", 0.30),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
    )
