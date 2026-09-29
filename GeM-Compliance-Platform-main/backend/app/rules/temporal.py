"""Deterministic certificate-validity-at-tender-closing rule."""

from datetime import date, datetime, timezone
from typing import Iterable

from app.models.domain import ComplianceResult, ComplianceStatus, Evidence, TenderRequirement, Verification

RULE_ID = "RULE-CERTIFICATE-VALID-AT-CLOSING"
FIELD_NAME = "certificate_valid_until"

def evaluate_certificate_validity_requirement(
    requirement: TenderRequirement,
    evidence: Iterable[Evidence],
    verifications: Iterable[Verification],
    *, bidder_id: str, result_id: str, tender_closing_date: date,
    evaluated_at: datetime | None = None, finding_ids: list[str] | None = None,
) -> ComplianceResult:
    if requirement.rule_id != RULE_ID:
        raise ValueError(f"Expected {RULE_ID!r}, got {requirement.rule_id!r}")
    verified = {v.evidence_id: v for v in verifications if v.status == "VERIFIED" and v.verified_value is not None}
    candidates = [e for e in evidence if e.requirement_id == requirement.id and e.field_name == FIELD_NAME and e.verification_status == "VERIFIED" and e.id in verified]
    timestamp = evaluated_at or datetime.now(timezone.utc)
    findings = finding_ids or []
    if not candidates:
        return ComplianceResult(
            id=result_id, tender_id=requirement.tender_id, bidder_id=bidder_id, requirement_id=requirement.id,
            status=ComplianceStatus.UNVERIFIABLE, rule_id=RULE_ID, expected=tender_closing_date.isoformat(),
            actual=None, evidence_ids=[], finding_ids=findings,
            explanation="No verified certificate validity date is currently available.", evaluated_at=timestamp,
        )
    evidence_item = sorted(candidates, key=lambda e: (e.page, e.id))[0]
    raw = verified[evidence_item.id].verified_value
    try:
        valid_until = date.fromisoformat(str(raw))
    except ValueError as exc:
        raise ValueError(f"Invalid certificate validity date {raw!r}") from exc
    passed = valid_until >= tender_closing_date
    return ComplianceResult(
        id=result_id, tender_id=requirement.tender_id, bidder_id=bidder_id, requirement_id=requirement.id,
        status=ComplianceStatus.PASS if passed else ComplianceStatus.FAIL, rule_id=RULE_ID,
        expected=tender_closing_date.isoformat(), actual=valid_until.isoformat(),
        evidence_ids=[evidence_item.id], finding_ids=findings,
        explanation=(f"Certificate remains valid through tender closing on {tender_closing_date.isoformat()}." if passed
                     else f"Certificate expires on {valid_until.isoformat()}, before tender closing on {tender_closing_date.isoformat()}."),
        evaluated_at=timestamp,
    )
