"""Tests for deterministic evidence trust report calculations."""

from app.citations.trust_report import build_trust_report


def _claim(status, claim="Example claim.", explanation="Test explanation.", sources=None):
    return {
        "claim": claim,
        "evidence_ids": ["E1"] if sources else [],
        "status": status,
        "explanation": explanation,
        "sources": sources or [],
    }


def test_all_supported_claims_have_100_percent_coverage():
    claims = [
        _claim("supported", "Claim one."),
        _claim("supported", "Claim two."),
    ]

    report = build_trust_report(claims)

    assert report["total_claims"] == 2
    assert report["supported"] == 2
    assert report["partially_supported"] == 0
    assert report["contradicted"] == 0
    assert report["insufficient"] == 0
    assert report["unsupported"] == 0
    assert report["coverage_percent"] == 100.0


def test_partial_support_counts_as_half_coverage():
    claims = [
        _claim("supported"),
        _claim("partially_supported"),
    ]

    report = build_trust_report(claims)

    assert report["coverage_percent"] == 75.0
    assert report["supported"] == 1
    assert report["partially_supported"] == 1


def test_contradicted_and_insufficient_claims_receive_zero_coverage():
    claims = [
        _claim("supported"),
        _claim("contradicted"),
        _claim("insufficient"),
    ]

    report = build_trust_report(claims)

    assert report["coverage_percent"] == 33.33
    assert report["contradicted"] == 1
    assert report["insufficient"] == 1
    assert report["unsupported"] == 2
    assert report["warnings"]


def test_empty_claim_list_has_no_coverage_score():
    report = build_trust_report([])

    assert report["total_claims"] == 0
    assert report["coverage_percent"] is None
    assert report["unsupported"] == 0
    assert report["warnings"]


def test_partial_contradicted_and_insufficient_claims_are_reported_as_gaps():
    claims = [
        _claim(
            "partially_supported",
            claim="The study improved every outcome.",
            explanation="Only one outcome was reported.",
        ),
        _claim(
            "contradicted",
            claim="The treatment was harmless.",
            explanation="The source reports adverse events.",
        ),
        _claim(
            "insufficient",
            claim="The treatment reduced mortality.",
            explanation="Mortality results were not provided.",
        ),
    ]

    report = build_trust_report(claims)

    assert len(report["gaps"]) == 3
    assert report["gaps"][0]["status"] == "partially_supported"
    assert report["gaps"][1]["status"] == "contradicted"
    assert report["gaps"][2]["status"] == "insufficient"
    assert report["gaps"][2]["explanation"] == "Mortality results were not provided."


def test_report_handles_unknown_status_safely():
    claims = [
        _claim("unknown_status"),
    ]

    report = build_trust_report(claims)

    assert report["total_claims"] == 1
    assert report["coverage_percent"] == 0.0
    assert report["unsupported"] == 1
    assert report["warnings"]
