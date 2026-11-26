
"""Offline tests for question coverage gap detection."""
import json

import pytest

from app.citations.evidence import Evidence
from app.citations.question_coverage import (
    analyze_question_coverage,
    build_question_coverage_prompt,
    parse_question_coverage_response,
)
from app.core.errors import LLMError
from tests.helpers import FakeLLM


@pytest.fixture
def evidence():
    return [
        Evidence(
            evidence_id="E1",
            document_id="doc_001",
            filename="library_policy.pdf",
            page=1,
            text="The library is open Monday through Friday, 9 AM to 6 PM.",
            score=0.9,
            chunk_id="chunk_001",
            chunk_index=0,
            char_start=0,
            char_end=60,
        ),
        Evidence(
            evidence_id="E2",
            document_id="doc_001",
            filename="library_policy.pdf",
            page=2,
            text="The library is open on Saturday from 10 AM to 2 PM.",
            score=0.8,
            chunk_id="chunk_002",
            chunk_index=1,
            char_start=61,
            char_end=112,
        ),
    ]


def test_prompt_includes_question_and_retrieved_evidence(evidence):
    prompt = build_question_coverage_prompt(
        "What are the weekday, Saturday, and Sunday hours?",
        evidence,
    )

    assert "Original user question:" in prompt
    assert "weekday, Saturday, and Sunday" in prompt
    assert "[E1]" in prompt
    assert "[E2]" in prompt
    assert "Monday through Friday" in prompt
    assert "Saturday from 10 AM to 2 PM" in prompt


def test_parser_counts_addressed_parts_and_gaps():
    response = json.dumps({
        "parts": [
            {
                "requested_part": "Weekday hours",
                "status": "no_gap",
                "explanation": "Weekday hours are explicitly stated.",
                "evidence_ids": ["E1"],
            },
            {
                "requested_part": "Saturday hours",
                "status": "no_gap",
                "explanation": "Saturday hours are explicitly stated.",
                "evidence_ids": ["E2"],
            },
            {
                "requested_part": "Sunday hours",
                "status": "missing_information",
                "explanation": "Sunday hours are not specified.",
                "evidence_ids": [],
            },
        ]
    })

    report = parse_question_coverage_response(response, {"E1", "E2"})

    assert report.total_parts == 3
    assert report.addressed_parts == 2
    assert report.unanswered_parts == 1
    assert len(report.gaps) == 1
    assert report.gaps[0].requested_part == "Sunday hours"
    assert report.gaps[0].status == "missing_information"
    assert report.gaps[0].evidence_ids == []


@pytest.mark.parametrize(
    "gap_status",
    [
        "missing_information",
        "incomplete_evidence",
        "conflicting_evidence",
    ],
)
def test_parser_accepts_all_gap_statuses(gap_status):
    response = json.dumps({
        "parts": [
            {
                "requested_part": "Requested information",
                "status": gap_status,
                "explanation": "The evidence does not fully resolve this request.",
                "evidence_ids": ["E1"],
            }
        ]
    })

    report = parse_question_coverage_response(response, {"E1"})

    assert report.total_parts == 1
    assert report.addressed_parts == 0
    assert report.unanswered_parts == 1
    assert report.gaps[0].status == gap_status
    assert report.gaps[0].evidence_ids == ["E1"]


def test_fabricated_evidence_ids_are_removed():
    response = json.dumps({
        "parts": [
            {
                "requested_part": "Library hours",
                "status": "incomplete_evidence",
                "explanation": "Evidence is incomplete.",
                "evidence_ids": ["E1", "E99", "E1"],
            }
        ]
    })

    report = parse_question_coverage_response(response, {"E1", "E2"})

    assert report.gaps[0].evidence_ids == ["E1"]


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError):
        parse_question_coverage_response("not JSON", {"E1"})


def test_empty_parts_are_rejected():
    with pytest.raises(ValueError):
        parse_question_coverage_response('{"parts": []}', {"E1"})


def test_unknown_status_is_rejected():
    response = json.dumps({
        "parts": [
            {
                "requested_part": "Library hours",
                "status": "maybe",
                "explanation": "Unknown classification.",
                "evidence_ids": [],
            }
        ]
    })

    with pytest.raises(ValueError):
        parse_question_coverage_response(response, {"E1"})


def test_missing_requested_part_is_rejected():
    response = json.dumps({
        "parts": [
            {
                "requested_part": "",
                "status": "missing_information",
                "explanation": "Missing request description.",
                "evidence_ids": [],
            }
        ]
    })

    with pytest.raises(ValueError):
        parse_question_coverage_response(response, {"E1"})


def test_coverage_analysis_uses_fake_llm(evidence):
    fake_llm = FakeLLM(json.dumps({
        "parts": [
            {
                "requested_part": "Weekday hours",
                "status": "no_gap",
                "explanation": "Weekday hours are in E1.",
                "evidence_ids": ["E1"],
            },
            {
                "requested_part": "Sunday hours",
                "status": "missing_information",
                "explanation": "Sunday hours are absent.",
                "evidence_ids": [],
            },
        ]
    }))

    report = analyze_question_coverage(
        "What are the weekday and Sunday hours?",
        evidence,
        fake_llm,
    )

    assert report is not None
    assert report.total_parts == 2
    assert report.addressed_parts == 1
    assert report.unanswered_parts == 1
    assert fake_llm.calls == 1


def test_coverage_llm_failure_is_nonfatal(evidence):
    fake_llm = FakeLLM(fail=True)

    report = analyze_question_coverage(
        "What are the weekday and Sunday hours?",
        evidence,
        fake_llm,
    )

    assert report is None
    assert fake_llm.calls == 1


def test_no_evidence_returns_none_without_calling_llm():
    fake_llm = FakeLLM("unused")

    report = analyze_question_coverage(
        "What are the opening hours?",
        [],
        fake_llm,
    )

    assert report is None
    assert fake_llm.calls == 0
