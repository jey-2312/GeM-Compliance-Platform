from pathlib import Path
from datetime import datetime, timezone

from app.models.domain import ComplianceStatus, Evidence, Verification
from app.rules.status import evaluate_status_requirement
from app.services.seed_loader import load_all_fixtures


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"
RUN_AT = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def _requirement(requirement_id: str):
    loaded = load_all_fixtures(FIXTURES)
    return next(r for r in loaded["requirements.json"] if r.id == requirement_id)


def _evaluate(requirement_id: str, field_name: str, value: str, *, status: str = "VERIFIED"):
    evidence = Evidence(
        id="EVD-STATUS-TEST",
        bidder_id="BIDDER-001",
        requirement_id=requirement_id,
        document_id="DOC-TEST",
        page=1,
        evidence_type="DOCUMENT_EXTRACT",
        field_name=field_name,
        value=value,
        source_label="Test document",
        confidence=0.98,
        verification_status=status,
    )
    verification = Verification(
        id="VER-STATUS-TEST",
        evidence_id=evidence.id,
        source_type="MOCK_GOVERNMENT_SOURCE",
        source_name="Test Mock Source",
        checked_at=RUN_AT,
        status=status,
        verified_value=value if status == "VERIFIED" else None,
        details="Test verification.",
    )
    return evaluate_status_requirement(
        _requirement(requirement_id),
        [evidence],
        [verification],
        bidder_id="BIDDER-001",
        result_id="CMP-STATUS-TEST",
        evaluated_at=RUN_AT,
    )


def test_gst_active_passes():
    result = _evaluate("REQ-002", "gst_status", "ACTIVE")
    assert result.status is ComplianceStatus.PASS
    assert result.actual == "ACTIVE"
    assert result.expected == "ACTIVE"


def test_pan_invalid_value_fails():
    result = _evaluate("REQ-003", "pan_status", "INVALID")
    assert result.status is ComplianceStatus.FAIL
    assert result.actual == "INVALID"
    assert result.expected == "VALID"


def test_udyam_missing_verification_is_unverifiable():
    result = _evaluate("REQ-004", "udyam_status", "ACTIVE", status="NOT_FOUND")
    assert result.status is ComplianceStatus.UNVERIFIABLE
    assert result.actual is None


def test_status_rule_does_not_accept_unverified_document_claim_as_verified():
    result = _evaluate("REQ-002", "gst_status", "ACTIVE", status="UNVERIFIED")
    assert result.status is ComplianceStatus.UNVERIFIABLE
    assert result.evidence_ids == []
