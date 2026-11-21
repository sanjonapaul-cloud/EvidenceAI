
"""Tests for claim-level verification utilities."""

from app.citations.evidence import build_evidence
from app.citations.verification import (
    Claim,
    build_verification_prompt,
    extract_claims,
    parse_verification_response,
)
from tests.helpers import SAMPLE_PAGES
from app.retrieval.base import RetrievedChunk


def _evidence():
    hits = [
        RetrievedChunk(
            "c1",
            "doc_001",
            "cool_roofs.pdf",
            3,
            SAMPLE_PAGES[3],
            0.9,
        ),
        RetrievedChunk(
            "c2",
            "doc_001",
            "cool_roofs.pdf",
            2,
            SAMPLE_PAGES[2],
            0.8,
        ),
    ]
    return build_evidence(hits)


def test_extract_claims_and_citation_ids():
    claims = extract_claims(
        "The study covered one city [E1]. "
        "Durability was not measured [E2]."
    )

    assert len(claims) == 2
    assert claims[0].text == "The study covered one city."
    assert claims[0].evidence_ids == ["E1"]
    assert claims[1].evidence_ids == ["E2"]


def test_claim_without_citation_is_still_detected():
    claims = extract_claims("The study proves the treatment works.")

    assert len(claims) == 1
    assert claims[0].evidence_ids == []


def test_multiple_citations_are_extracted():
    claims = extract_claims("The study had limitations [E1, E2].")

    assert claims[0].evidence_ids == ["E1", "E2"]


def test_verification_prompt_contains_only_claim_evidence():
    evidence = _evidence()
    claim = Claim(
        text="The study covered one city.",
        evidence_ids=["E1"],
    )

    prompt = build_verification_prompt(claim, evidence)

    assert "The study covered one city." in prompt
    assert "[E1]" in prompt
    assert "[E2]" not in prompt
    assert "Use ONLY the supplied evidence" in prompt


def test_valid_verification_response_is_parsed():
    claim = Claim("The study covered one city.", ["E1"])

    result = parse_verification_response(
        '{"status": "supported", '
        '"explanation": "The passage explicitly states this."}',
        claim,
    )

    assert result is not None
    assert result.status == "supported"
    assert result.evidence_ids == ["E1"]


def test_all_verification_statuses_are_accepted():
    claim = Claim("Example claim.", ["E1"])

    for status in (
        "supported",
        "partially_supported",
        "contradicted",
        "insufficient",
    ):
        result = parse_verification_response(
            (
                '{"status": "' + status
                + '", "explanation": "Test explanation."}'
            ),
            claim,
        )
        assert result is not None
        assert result.status == status


def test_invalid_verifier_response_is_rejected():
    claim = Claim("Example claim.", ["E1"])

    assert parse_verification_response("not JSON", claim) is None

    assert parse_verification_response(
        '{"status": "probably_true", "explanation": "Looks right."}',
        claim,
    ) is None

    assert parse_verification_response(
        '{"status": "supported", "explanation": ""}',
        claim,
    ) is None
