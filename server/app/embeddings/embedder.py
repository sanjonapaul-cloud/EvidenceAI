"""Sentence Transformers embeddings (Member 4).

An "embedding" is a list of numbers that represents the meaning of a piece of
text. Texts with similar meaning get similar numbers, which is how we find
relevant chunks for a question.

The model is loaded lazily (the first time it is needed) so the web server
starts quickly. The first load downloads the model from Hugging Face, which
needs an internet connection and may take a minute.
"""
from __future__ import annotations

import logging
import threading

from app.core.errors import EmbeddingError

logger = logging.getLogger("evidenceai.embeddings")


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:
                        raise EmbeddingError(
                            "sentence-transformers is not installed. "
                            "Run: pip install -r requirements.txt"
                        ) from exc
                    try:
                        logger.info("Loading embedding model %s ...", self.model_name)
                        self._model = SentenceTransformer(self.model_name)
                    except Exception as exc:
                        logger.exception("Could not load embedding model")
                        raise EmbeddingError(
                            "The embedding model could not be loaded. The first run needs an "
                            "internet connection to download it."
                        ) from exc
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            vectors = self._get_model().encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            return [list(map(float, v)) for v in vectors]
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.exception("Embedding failed")
            raise EmbeddingError("Creating embeddings failed.") from exc

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
