"""Deterministic evidence coverage and trust report calculations."""

from __future__ import annotations

from typing import Any


def build_trust_report(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an evidence coverage report from claim verification results.

    Coverage weights:
        supported: 1.0
        partially_supported: 0.5
        contradicted: 0.0
        insufficient: 0.0
        unknown statuses: 0.0

    This is an evidence coverage metric, not a probability of correctness.
    """
    supported = 0
    partially_supported = 0
    contradicted = 0
    insufficient = 0
    unknown = 0
    gaps: list[dict[str, Any]] = []

    for claim in claims:
        status = claim.get("status", "unknown")

        if status == "supported":
            supported += 1

        elif status == "partially_supported":
            partially_supported += 1
            gaps.append(claim)

        elif status == "contradicted":
            contradicted += 1
            gaps.append(claim)

        elif status == "insufficient":
            insufficient += 1
            gaps.append(claim)

        else:
            unknown += 1
            gaps.append(claim)

    total_claims = len(claims)
    unsupported = contradicted + insufficient + unknown

    if total_claims == 0:
        coverage_percent = None
    else:
        coverage = supported + (0.5 * partially_supported)
        coverage_percent = round((coverage / total_claims) * 100, 2)

    warnings: list[str] = []

    if total_claims == 0:
        warnings.append("No claims were available to calculate evidence coverage.")

    if partially_supported:
        warnings.append(
            f"{partially_supported} claim(s) are only partially supported by evidence."
        )

    if contradicted:
        warnings.append(
            f"{contradicted} claim(s) are contradicted by the available evidence."
        )

    if insufficient:
        warnings.append(
            f"{insufficient} claim(s) have insufficient evidence."
        )

    if unknown:
        warnings.append(
            f"{unknown} claim(s) have an unrecognized verification status."
        )

    return {
        "total_claims": total_claims,
        "supported": supported,
        "partially_supported": partially_supported,
        "contradicted": contradicted,
        "insufficient": insufficient,
        "unsupported": unsupported,
        "coverage_percent": coverage_percent,
        "gaps": gaps,
        "warnings": warnings,
    }
