from datetime import datetime, timezone, date
from pathlib import Path

from app.models.domain import ComplianceStatus, Evidence, Verification
from app.rules.temporal import evaluate_certificate_validity_requirement
from app.rules.turnover import evaluate_greater_than_or_equal_requirement
from app.services.seed_loader import load_all_fixtures

FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"
RUN_AT = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

def _req(rid):
    loaded=load_all_fixtures(FIXTURES)
    return next(r for r in loaded["requirements.json"] if r.id==rid)

def test_tender_a_local_content_fails_with_materiality_gap():
    loaded=load_all_fixtures(FIXTURES)
    req=_req("REQ-TND-001-010")
    result=evaluate_greater_than_or_equal_requirement(req, loaded["evidence.json"], loaded["verifications.json"], bidder_id="BIDDER-001", result_id="CMP-LC-A", evaluated_at=RUN_AT)
    assert result.status is ComplianceStatus.FAIL
    assert result.actual == 42
    assert result.expected == 50
    assert result.gap_to_compliance == "Needs 8 percentage points more local content to pass."

def test_tender_b_local_content_passes():
    loaded=load_all_fixtures(FIXTURES)
    req=_req("REQ-TND-002-009")
    result=evaluate_greater_than_or_equal_requirement(req, loaded["evidence.json"], loaded["verifications.json"], bidder_id="BIDDER-001", result_id="CMP-LC-B", evaluated_at=RUN_AT)
    assert result.status is ComplianceStatus.PASS
    assert result.actual == 55

def test_certificate_is_valid_at_tender_closing():
    loaded=load_all_fixtures(FIXTURES)
    req=_req("REQ-TND-002-018")
    result=evaluate_certificate_validity_requirement(req, loaded["evidence.json"], loaded["verifications.json"], bidder_id="BIDDER-001", result_id="CMP-TEMP", tender_closing_date=date(2026,11,12), evaluated_at=RUN_AT)
    assert result.status is ComplianceStatus.PASS
    assert result.actual == "2026-12-15"

def test_certificate_expiry_before_closing_fails():
    req=_req("REQ-TND-002-018")
    evidence=[Evidence(id="EVD-TEMP", bidder_id="BIDDER-001", requirement_id=req.id, document_id="DOC-TEST", page=1, evidence_type="DOCUMENT_EXTRACT", field_name="certificate_valid_until", value="2026-10-01", source_label="Test certificate", confidence=0.98, verification_status="VERIFIED")]
    verifications=[Verification(id="VER-TEMP", evidence_id="EVD-TEMP", source_type="MOCK_DOCUMENT_VERIFICATION", source_name="Test", checked_at=RUN_AT, status="VERIFIED", verified_value="2026-10-01", details="Test")]
    result=evaluate_certificate_validity_requirement(req, evidence, verifications, bidder_id="BIDDER-001", result_id="CMP-TEMP-FAIL", tender_closing_date=date(2026,11,12), evaluated_at=RUN_AT)
    assert result.status is ComplianceStatus.FAIL
    assert "2026-10-01" in result.explanation
