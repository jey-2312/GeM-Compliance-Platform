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


def _verified_turnover_evidence(
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
) -> tuple[Evidence, Verification] | None:
    """Return the first turnover evidence with a VERIFIED verification record."""

    verification_by_evidence = {
        verification.evidence_id: verification
        for verification in verifications
        if verification.status == "VERIFIED"
        and verification.verified_value is not None
    }

    for item in evidence:
        if item.field_name != FIELD_NAME or item.verification_status != "VERIFIED":
            continue
        verification = verification_by_evidence.get(item.id)
        if verification is not None:
            return item, verification

    return None


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
    """Evaluate verified turnover against the tender threshold.

    Rules:
    - Missing verified turnover -> UNVERIFIABLE.
    - Verified actual >= threshold -> PASS.
    - Verified actual < threshold -> FAIL.

    The evaluator does not inspect self-declared values or infer fraud.
    Contradiction findings are separate from the compliance decision.
    """

    if requirement.rule_id != RULE_ID:
        raise ValueError(
            f"Expected requirement.rule_id={RULE_ID!r}, got {requirement.rule_id!r}"
        )

    if requirement.type != "TURNOVER":
        raise ValueError(
            f"Expected requirement.type='TURNOVER', got {requirement.type!r}"
        )

    if requirement.operator != OPERATOR:
        raise ValueError(
            f"Expected operator={OPERATOR!r}, got {requirement.operator!r}"
        )

    if requirement.threshold is None:
        raise ValueError("TURNOVER requirement must provide a threshold")

    verified = _verified_turnover_evidence(evidence, verifications)
    timestamp = evaluated_at or datetime.now(timezone.utc)
    findings = finding_ids or []

    if verified is None:
        return ComplianceResult(
            id=result_id,
            tender_id=requirement.tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement.id,
            status=ComplianceStatus.UNVERIFIABLE,
            rule_id=RULE_ID,
            expected=requirement.threshold,
            actual=None,
            evidence_ids=[],
            finding_ids=findings,
            explanation=(
                "No verified average annual turnover evidence is currently available."
            ),
            evaluated_at=timestamp,
        )

    evidence_item, verification = verified
    actual = verification.verified_value

    if not isinstance(actual, (int, float)) or isinstance(actual, bool):
        raise ValueError("Verified turnover value must be numeric")

    passed = actual >= requirement.threshold
    status = ComplianceStatus.PASS if passed else ComplianceStatus.FAIL

    explanation = (
        f"Verified turnover of INR {actual} meets the tender minimum of "
        f"INR {requirement.threshold}."
        if passed
        else f"Verified turnover of INR {actual} is below the tender minimum of "
        f"INR {requirement.threshold}."
    )

    return ComplianceResult(
        id=result_id,
        tender_id=requirement.tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement.id,
        status=status,
        rule_id=RULE_ID,
        expected=requirement.threshold,
        actual=actual,
        evidence_ids=[evidence_item.id],
        finding_ids=findings,
        explanation=explanation,
        evaluated_at=timestamp,
    )

