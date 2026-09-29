"""Deterministic RULE-TURNOVER-GTE evaluator."""

from datetime import datetime, timezone
from typing import Iterable

from app.models.domain import (
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    TenderRequirement,
    Verification,
)

RULE_ID = "RULE-TURNOVER-GTE"
FIELD_NAME = "average_annual_turnover"
OPERATOR = "GREATER_THAN_OR_EQUAL"
NUMERIC_GTE_RULES = {
    "RULE-TURNOVER-GTE": ("average_annual_turnover", "INR"),
    "RULE-LOCAL-CONTENT-GTE": ("local_content_percentage", "%"),
}


def _verified_numeric_evidence(
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
    *,
    field_name: str,
    requirement_id: str | None = None,
) -> tuple[Evidence, Verification] | None:
    verification_by_evidence = {
        verification.evidence_id: verification
        for verification in verifications
        if verification.status == "VERIFIED" and verification.verified_value is not None
    }
    for item in evidence:
        if (requirement_id is not None and item.requirement_id != requirement_id) or item.field_name != field_name or item.verification_status != "VERIFIED":
            continue
        verification = verification_by_evidence.get(item.id)
        if verification is not None:
            return item, verification
    return None


def evaluate_greater_than_or_equal_requirement(
    requirement: TenderRequirement,
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
    *,
    bidder_id: str,
    result_id: str,
    evaluated_at: datetime | None = None,
    finding_ids: list[str] | None = None,
) -> ComplianceResult:
    """Evaluate a numeric >= requirement using verified evidence only."""
    rule_definition = NUMERIC_GTE_RULES.get(requirement.rule_id)
    if rule_definition is None:
        raise ValueError(f"Unsupported numeric GTE rule {requirement.rule_id!r}")
    field_name, unit = rule_definition
    if requirement.operator != OPERATOR:
        raise ValueError(f"Expected operator={OPERATOR!r}, got {requirement.operator!r}")
    if requirement.threshold is None:
        raise ValueError("Numeric GTE requirement must provide a threshold")

    verified = _verified_numeric_evidence(
        evidence, verifications, field_name=field_name,
        requirement_id=requirement.id if requirement.rule_id == "RULE-LOCAL-CONTENT-GTE" else None,
    )
    timestamp = evaluated_at or datetime.now(timezone.utc)
    findings = finding_ids or []
    if verified is None:
        return ComplianceResult(
            id=result_id, tender_id=requirement.tender_id, bidder_id=bidder_id,
            requirement_id=requirement.id, status=ComplianceStatus.UNVERIFIABLE,
            rule_id=requirement.rule_id, expected=requirement.threshold, actual=None,
            evidence_ids=[], finding_ids=findings,
            explanation=f"No verified {field_name} evidence is currently available.",
            evaluated_at=timestamp,
        )

    evidence_item, verification = verified
    actual = verification.verified_value
    if not isinstance(actual, (int, float)) or isinstance(actual, bool):
        raise ValueError(f"Verified {field_name} value must be numeric")
    passed = actual >= requirement.threshold
    status = ComplianceStatus.PASS if passed else ComplianceStatus.FAIL
    if unit == "INR":
        explanation = (
            f"Verified turnover of INR {actual} meets the tender minimum of INR {requirement.threshold}."
            if passed else
            f"Verified turnover of INR {actual} is below the tender minimum of INR {requirement.threshold}."
        )
        gap = None if passed else f"Needs INR {requirement.threshold - actual:,.0f} more in verified turnover to pass."
    else:
        explanation = (
            f"Verified local content of {actual}% meets the tender minimum of {requirement.threshold}%."
            if passed else
            f"Verified local content of {actual}% is below the tender minimum of {requirement.threshold}%."
        )
        gap = None if passed else f"Needs {requirement.threshold - actual:g} percentage points more local content to pass."
    return ComplianceResult(
        id=result_id, tender_id=requirement.tender_id, bidder_id=bidder_id,
        requirement_id=requirement.id, status=status, rule_id=requirement.rule_id,
        expected=requirement.threshold, actual=actual, evidence_ids=[evidence_item.id],
        finding_ids=findings, explanation=explanation, evaluated_at=timestamp,
        gap_to_compliance=gap,
    )


def evaluate_turnover_requirement(
    requirement: TenderRequirement,
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
    *,
    bidder_id: str,
    result_id: str,
    evaluated_at: datetime | None = None,
    finding_ids: list[str] | None = None,
) -> ComplianceResult:
    """Compatibility wrapper for the canonical turnover evaluator."""
    if requirement.rule_id != RULE_ID or requirement.type != "TURNOVER":
        raise ValueError(
            f"Expected TURNOVER/RULE-TURNOVER-GTE, got type={requirement.type!r}, rule={requirement.rule_id!r}"
        )
    return evaluate_greater_than_or_equal_requirement(
        requirement, evidence, verifications, bidder_id=bidder_id, result_id=result_id,
        evaluated_at=evaluated_at, finding_ids=finding_ids,
    )

