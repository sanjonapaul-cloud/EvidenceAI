"""Small fake components so tests run without downloading models or calling Gemini.

HashingEmbedder is NOT a real semantic model: it only matches shared words. It is used to test
the *plumbing* (metadata, thresholds, status handling). Retrieval *quality* with the real
Sentence Transformers model must be checked by hand (see docs/testing_guide.md).
"""
from __future__ import annotations

import hashlib
import math
import re

from app.core.config import Settings
from app.core.errors import LLMError
from app.retrieval.base import RetrievedChunk

STOPWORDS = {"the", "a", "an", "of", "to", "and", "in", "is", "are", "what", "was", "were", "for", "on", "by", "with", "this", "that", "it", "as", "at"}
DIMS = 512


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


class HashingEmbedder:
    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * DIMS
        for word in tokenize(text):
            idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMS
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


class InMemoryVectorStore:
    """Same interface as ChromaVectorStore, kept in a Python list."""

    def __init__(self):
        self.rows = []  # (chunk, embedding)

    def add_chunks(self, chunks, embeddings):
        self.rows.extend(zip(chunks, embeddings))

    def query(self, embedding, top_k, document_ids=None):
        scored = []
        for chunk, emb in self.rows:
            if document_ids and chunk.document_id not in document_ids:
                continue
            score = sum(a * b for a, b in zip(embedding, emb))  # cosine (vectors are unit length)
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page=chunk.page,
                    text=chunk.text,
                    score=score,
                    chunk_index=chunk.chunk_index,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def delete_document(self, document_id):
        self.rows = [(c, e) for c, e in self.rows if c.document_id != document_id]

    def count(self):
        return len(self.rows)


class FakeLLM:
    def __init__(self, reply="", configured=True, fail=False):
        self.reply = reply
        self.responses = (
            list(reply) if isinstance(reply, (list, tuple)) else [reply]
        )
        self.is_configured = configured
        self.fail = fail
        self.calls = 0
        self.last_prompt = None
        self.prompts = []

    def generate(self, system_instruction, prompt):
        self.calls += 1
        self.last_prompt = prompt
        self.prompts.append((system_instruction, prompt))

        if self.fail:
            raise LLMError("boom")

        if not self.responses:
            return ""

        response_index = min(self.calls - 1, len(self.responses) - 1)
        return self.responses[response_index]


# A tiny fake "PDF" content: pages of text used by fake extractors.
SAMPLE_PAGES = {
    1: "Cool roofs reflect sunlight and lower rooftop surface temperature in dense neighbourhoods. "
    "The pilot study compared reflective coatings with standard dark roofing on forty buildings.",
    2: "Sensors recorded air temperature every ten minutes during the summer measurement period. "
    "Researchers used paired buildings to compare reflective and standard roofs fairly.",
    3: "Limitations: the study covered a single city and only one summer, so results may not "
    "generalise. Coating durability over several years was not measured.",
}
def make_settings(tmp_path, **overrides) -> Settings:
    values = dict(
        gemini_api_key="",
        audit_api_key="",
        gemini_model="test-model",
        embedding_model="test-embedder",
        data_dir=tmp_path,
        max_upload_mb=1,
        chunk_size=300,
        chunk_overlap=50,
        top_k=5,
        min_relevance_score=0.2,
        cors_origins=["http://localhost:5173"],
    )
    values.update(overrides)
    return Settings(**values)
