"""Deterministic status-rule evaluators for the prototype.

These evaluators cover the status checks already present in the canonical
prototype requirements: GST ACTIVE, PAN VALID, and Udyam ACTIVE.
The evaluator consumes verified evidence only and never calls an LLM.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.models.domain import (
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    TenderRequirement,
    Verification,
)


STATUS_RULES: dict[str, dict[str, str]] = {
    "RULE-GST-ACTIVE": {"field": "gst_status", "expected": "ACTIVE"},
    "RULE-PAN-VALID": {"field": "pan_status", "expected": "VALID"},
    "RULE-UDYAM-ACTIVE": {"field": "udyam_status", "expected": "ACTIVE"},
}


def evaluate_status_requirement(
    requirement: TenderRequirement,
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
    *,
    bidder_id: str,
    result_id: str,
    evaluated_at: datetime | None = None,
    finding_ids: list[str] | None = None,
) -> ComplianceResult:
    """Evaluate one supported status requirement from verified evidence."""

    try:
        definition = STATUS_RULES[requirement.rule_id]
    except KeyError as exc:
        raise ValueError(
            f"No deterministic status evaluator is registered for {requirement.rule_id!r}."
        ) from exc

    expected = definition["expected"]
    field_name = definition["field"]
    timestamp = evaluated_at or datetime.now(timezone.utc)
    findings = finding_ids or []

    verification_by_evidence: dict[str, Verification] = {}
    for verification in verifications:
        if verification.status != "VERIFIED" or verification.verified_value is None:
            continue
        previous = verification_by_evidence.get(verification.evidence_id)
        if previous is None or verification.checked_at > previous.checked_at:
            verification_by_evidence[verification.evidence_id] = verification

    candidates = [
        item
        for item in evidence
        if item.field_name == field_name
        and item.verification_status == "VERIFIED"
        and item.id in verification_by_evidence
    ]

    if not candidates:
        return ComplianceResult(
            id=result_id,
            tender_id=requirement.tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement.id,
            status=ComplianceStatus.UNVERIFIABLE,
            rule_id=requirement.rule_id,
            expected=expected,
            actual=None,
            evidence_ids=[],
            finding_ids=findings,
            explanation=(
                f"No verified {field_name} evidence is currently available."
            ),
            evaluated_at=timestamp,
        )

    candidate = sorted(candidates, key=lambda item: (item.page, item.id))[0]
    verification = verification_by_evidence[candidate.id]
    actual = verification.verified_value

    if not isinstance(actual, str):
        raise ValueError(
            f"Verified {field_name} value must be a string; got {type(actual).__name__}."
        )

    passed = actual.strip().casefold() == expected.casefold()
    status = ComplianceStatus.PASS if passed else ComplianceStatus.FAIL

    explanation = (
        f"Verified {field_name} status is {actual!r}, which matches the required "
        f"status {expected!r}."
        if passed
        else f"Verified {field_name} status is {actual!r}, which does not match the "
        f"required status {expected!r}."
    )

    return ComplianceResult(
        id=result_id,
        tender_id=requirement.tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement.id,
        status=status,
        rule_id=requirement.rule_id,
        expected=expected,
        actual=actual,
        evidence_ids=[candidate.id],
        finding_ids=findings,
        explanation=explanation,
        evaluated_at=timestamp,
    )
