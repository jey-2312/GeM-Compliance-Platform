from datetime import datetime, timezone
from pathlib import Path

from app.models.domain import ComplianceStatus
from app.services.workflow_service import WorkflowService


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"
RUN_AT = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def _service() -> WorkflowService:
    return WorkflowService.from_fixtures(FIXTURES)


def test_tender_a_runs_complete_evidence_backed_workflow():
    service = _service()
    report = service.run(
        tender_id="TND-001",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )

    results = report["compliance_results"]
    assert len(results) == 4

    by_requirement = {item["requirement_id"]: item for item in results}
    assert by_requirement["REQ-001"]["status"] == ComplianceStatus.FAIL.value
    assert by_requirement["REQ-001"]["actual"] == 48_000_000
    assert by_requirement["REQ-001"]["expected"] == 50_000_000
    assert by_requirement["REQ-001"]["finding_ids"]
    assert by_requirement["REQ-002"]["status"] == ComplianceStatus.PASS.value
    assert by_requirement["REQ-003"]["status"] == ComplianceStatus.PASS.value
    assert by_requirement["REQ-004"]["status"] == ComplianceStatus.PASS.value

    turnover_chain = report["evidence_chains"][by_requirement["REQ-001"]["id"]]
    assert turnover_chain["requirement"]["id"] == "REQ-001"
    assert turnover_chain["rule"]["id"] == "RULE-TURNOVER-GTE"
    assert turnover_chain["evidence"]
    assert any(
        node["document"]["id"] == "DOC-001" and node["page"] == 12
        for node in turnover_chain["evidence"]
    )
    assert turnover_chain["compliance"]["status"] == "FAIL"
    assert turnover_chain["audit"]["action"] == "COMPLIANCE_EVALUATED"


def test_tender_b_reuses_same_bidder_evidence_and_changes_only_tender_result():
    service = _service()
    report = service.run(
        tender_id="TND-002",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )

    results = {item["requirement_id"]: item for item in report["compliance_results"]}
    assert len(results) == 4
    assert results["REQ-005"]["status"] == ComplianceStatus.PASS.value
    assert results["REQ-005"]["actual"] == 48_000_000
    assert results["REQ-005"]["expected"] == 30_000_000
    assert results["REQ-006"]["status"] == ComplianceStatus.PASS.value
    assert results["REQ-007"]["status"] == ComplianceStatus.PASS.value
    assert results["REQ-008"]["status"] == ComplianceStatus.PASS.value

    assert report["summary"] == {"PASS": 4}


def test_passport_mock_verifications_are_visible_in_workflow_report():
    service = _service()
    report = service.run(
        tender_id="TND-001",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )

    statuses = {item["source_name"]: item["status"] for item in report["passport_verifications"]}
    assert statuses["Mock GST Verification"] == "VERIFIED"
    assert statuses["Mock PAN Verification"] == "VERIFIED"
    assert statuses["Mock Udyam Verification"] == "VERIFIED"
    assert all(
        item["source_type"] == "MOCK_GOVERNMENT_SOURCE"
        for item in report["passport_verifications"]
    )


def test_two_tender_run_creates_tender_specific_evidence_for_reused_status_records():
    service = _service()
    reports = service.run_both_demo_tenders(
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )

    a_evidence = {
        item["id"]
        for item in reports["TND-001"]["evidence"]
        if item["field_name"] in {"gst_status", "pan_status", "udyam_status"}
    }
    b_evidence = {
        item["id"]
        for item in reports["TND-002"]["evidence"]
        if item["field_name"] in {"gst_status", "pan_status", "udyam_status"}
    }
    assert a_evidence
    assert b_evidence
    assert a_evidence.isdisjoint(b_evidence)


def test_audit_history_contains_one_event_per_evaluated_requirement():
    service = _service()
    service.run(
        tender_id="TND-001",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )
    history = service.get_audit_history("TND-001", "BIDDER-001")
    assert len(history) == 4
    assert all(event.action == "COMPLIANCE_EVALUATED" for event in history)


def test_repeated_workflow_run_does_not_duplicate_evidence_or_verifications():
    service = _service()
    first = service.run(
        tender_id="TND-002",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )
    evidence_count = len(service.evidence_engine.get_all_evidence())
    verification_count = len(service.evidence_engine.get_all_verifications())

    second = service.run(
        tender_id="TND-002",
        bidder_id="BIDDER-001",
        evaluated_at=RUN_AT,
    )

    assert [item["id"] for item in first["evidence"]] == [
        item["id"] for item in second["evidence"]
    ]
    assert len(service.evidence_engine.get_all_evidence()) == evidence_count
    assert len(service.evidence_engine.get_all_verifications()) == verification_count
    assert second["summary"] == {"PASS": 4}
