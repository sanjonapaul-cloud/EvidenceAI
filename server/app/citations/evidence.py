"""Evidence IDs and citation validation (Member 5).

How citations stay honest:
1. Only chunks that were really retrieved become "evidence" (E1, E2, ...).
2. The LLM may only reference those IDs, written like [E1].
3. After the LLM answers, we CHECK every [E#] it used. IDs that do not exist
   are removed, and the citation cards are built from our own stored chunks,
   never from text the LLM wrote. So a citation can never contain an invented
   filename, page number or excerpt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from app.retrieval.base import RetrievedChunk

EXCERPT_MAX_CHARS = 300

# Matches [E1], [E1, E2], [E1; E3]
_MARKER = re.compile(r"\[\s*(E\d+(?:\s*[,;]\s*E\d+)*)\s*\]", re.IGNORECASE)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    document_id: str
    filename: str
    page: int
    text: str
    score: float
    chunk_id: str
    chunk_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass
class CitationCheck:
    clean_answer: str  # answer with invalid [E#] markers removed
    cited: list[Evidence]  # evidence that the answer validly referenced, in order of first use
    invalid_ids: list[str]  # IDs the model used that do not exist


def build_evidence(hits: Sequence[RetrievedChunk]) -> list[Evidence]:
    """Number retrieved chunks E1, E2, ... in relevance order."""
    return [
        Evidence(
            evidence_id=f"E{i}",
            document_id=h.document_id,
            filename=h.filename,
            page=h.page,
            text=h.text,
            score=h.score,
            chunk_id=h.chunk_id,
            chunk_index=h.chunk_index,
            char_start=h.char_start,
            char_end=h.char_end,
        )
        for i, h in enumerate(hits, start=1)
    ]


def make_excerpt(text: str, max_chars: int = EXCERPT_MAX_CHARS) -> str:
    """The start of the stored chunk text, cut at a word boundary. Always real source text."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut + "…"


def evidence_to_citation(ev: Evidence) -> dict:
    return {
        "document_id": ev.document_id,
        "filename": ev.filename,
        "page": ev.page,
        "evidence_id": ev.evidence_id,
        "excerpt": make_excerpt(ev.text),
        "chunk_id": ev.chunk_id,
        "chunk_index": ev.chunk_index,
        "char_start": ev.char_start,
        "char_end": ev.char_end,
    }


def extract_cited_ids(answer: str) -> list[str]:
    """All evidence IDs used in the answer, upper-cased, in order, without duplicates."""
    seen: list[str] = []
    for match in _MARKER.finditer(answer):
        for raw in re.split(r"[,;]", match.group(1)):
            eid = raw.strip().upper()
            if eid and eid not in seen:
                seen.append(eid)
    return seen


def validate_answer_citations(answer: str, evidence: Sequence[Evidence]) -> CitationCheck:
    """Check the model's [E#] markers against the evidence we really provided."""
    by_id = {e.evidence_id: e for e in evidence}
    invalid: list[str] = []

    def _rewrite(match: re.Match) -> str:
        ids = [x.strip().upper() for x in re.split(r"[,;]", match.group(1))]
        good = [i for i in ids if i in by_id]
        invalid.extend(i for i in ids if i not in by_id and i not in invalid)
        return f"[{', '.join(good)}]" if good else ""

    clean = _MARKER.sub(_rewrite, answer)
    clean = re.sub(r"[ \t]{2,}", " ", clean).strip()
    cited = [by_id[i] for i in extract_cited_ids(clean) if i in by_id]
    return CitationCheck(clean_answer=clean, cited=cited, invalid_ids=invalid)
