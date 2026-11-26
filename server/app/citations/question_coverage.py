
"""Detect unanswered parts of a user's question against retrieved evidence."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from app.citations.evidence import Evidence
from app.core.errors import LLMError
from app.schemas import QuestionCoverageReport, QuestionGap

logger = logging.getLogger(__name__)


COVERAGE_SYSTEM_INSTRUCTION = """You are an evidence coverage analyzer for a document-grounded
question-answering system.

Your task is to identify every distinct information request contained in the user's
original question and evaluate whether the supplied evidence addresses it.

Rules:
- Use ONLY the supplied evidence passages.
- Break multi-part questions into distinct, answerable requested parts.
- A part is addressed only when the evidence adequately answers it.
- Do not assume information that is not explicitly supported.
- Missing information means the evidence does not contain the requested information.
- Incomplete evidence means some relevant information exists but does not fully
  answer the requested part.
- Conflicting evidence means supplied passages disagree about the requested part.
- Do not invent evidence IDs.
- Do not treat the generated answer as evidence.
- Do not infer that a topic is covered merely because it is mentioned.
- For a fully addressed part, use status "no_gap".
- For gaps, use "missing_information", "incomplete_evidence", or
  "conflicting_evidence".
- Return ONLY valid JSON. No markdown fences or additional prose.

Required JSON format:
{
  "parts": [
    {
      "requested_part": "A distinct part of the user's question",
      "status": "no_gap",
      "explanation": "Why the evidence addresses this part",
      "evidence_ids": ["E1"]
    },
    {
      "requested_part": "Another requested part",
      "status": "missing_information",
      "explanation": "The supplied evidence does not specify this information",
      "evidence_ids": []
    }
  ]
}
"""


def build_question_coverage_prompt(
    question: str,
    evidence: list[Evidence],
) -> str:
    """Build a coverage-analysis prompt using only retrieved passages."""
    passages = []

    for item in evidence:
        passages.append(
            f"[{item.evidence_id}] "
            f"(file: {item.filename}, page: {item.page})\n"
            f"{item.text}"
        )

    evidence_text = "\n\n".join(passages) or "(No evidence passages supplied.)"

    return (
        f"Original user question:\n{question}\n\n"
        f"Retrieved evidence passages:\n{evidence_text}\n\n"
        "Analyze question coverage and return the required JSON."
    )


def _extract_json(text: str) -> dict:
    """Parse JSON, allowing a surrounding markdown code fence if present."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    parsed = json.loads(cleaned)

    if not isinstance(parsed, dict):
        raise ValueError("Coverage response must be a JSON object.")

    return parsed


def parse_question_coverage_response(
    response: str,
    valid_evidence_ids: set[str],
) -> QuestionCoverageReport:
    """Validate an LLM coverage response and discard fabricated evidence IDs."""
    data = _extract_json(response)
    raw_parts = data.get("parts")

    if not isinstance(raw_parts, list) or not raw_parts:
        raise ValueError("Coverage response must contain a non-empty parts list.")

    addressed = 0
    gaps: list[QuestionGap] = []
    total_parts = 0

    for raw_part in raw_parts:
        if not isinstance(raw_part, dict):
            raise ValueError("Each coverage part must be a JSON object.")

        requested_part = raw_part.get("requested_part")
        status = raw_part.get("status")
        explanation = raw_part.get("explanation")
        evidence_ids = raw_part.get("evidence_ids", [])

        if not isinstance(requested_part, str) or not requested_part.strip():
            raise ValueError("Each requested part must have a non-empty description.")

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("Each coverage part must have an explanation.")

        if not isinstance(evidence_ids, list) or not all(
            isinstance(item, str) for item in evidence_ids
        ):
            raise ValueError("Evidence IDs must be a list of strings.")

        # Only accept evidence IDs that actually exist in the retrieved evidence.
        valid_ids = list(dict.fromkeys(
            item for item in evidence_ids if item in valid_evidence_ids
        ))

        total_parts += 1

        if status == "no_gap":
            addressed += 1
            continue

        if status not in {
            "missing_information",
            "incomplete_evidence",
            "conflicting_evidence",
        }:
            raise ValueError(f"Unknown coverage status: {status!r}")

        gaps.append(
            QuestionGap(
                requested_part=requested_part.strip(),
                status=status,
                explanation=explanation.strip(),
                evidence_ids=valid_ids,
            )
        )

    return QuestionCoverageReport(
        total_parts=total_parts,
        addressed_parts=addressed,
        unanswered_parts=len(gaps),
        gaps=gaps,
    )


def analyze_question_coverage(
    question: str,
    evidence: list[Evidence],
    llm,
) -> Optional[QuestionCoverageReport]:
    """Analyze coverage. Failure is non-fatal to the main answer pipeline."""
    if not evidence:
        return None

    prompt = build_question_coverage_prompt(question, evidence)

    try:
        response = llm.generate(COVERAGE_SYSTEM_INSTRUCTION, prompt)
        valid_ids = {item.evidence_id for item in evidence}
        return parse_question_coverage_response(response, valid_ids)
    except (LLMError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning(
            "Question coverage analysis failed (%s).",
            type(exc).__name__,
        )
        return None
