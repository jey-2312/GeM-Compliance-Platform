from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.state import AppState
from app.main import create_app
from app.services.workflow_service import WorkflowService
from app.verification.service import VerificationService


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"
RUN_AT = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def _client() -> TestClient:
    workflow = WorkflowService.from_fixtures(FIXTURES)
    state = AppState(workflow=workflow, verification=VerificationService(mode="mock"))
    return TestClient(create_app(state))


def test_health_and_discovery_endpoints():
    client = _client()

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["verification_mode"] == "mock"

    tenders = client.get("/api/v1/tenders")
    assert tenders.status_code == 200
    assert [item["id"] for item in tenders.json()] == ["TND-001", "TND-002"]

    requirements = client.get("/api/v1/tenders/TND-001/requirements")
    assert requirements.status_code == 200
    assert len(requirements.json()) == 18

    bidder = client.get("/api/v1/bidders/BIDDER-001")
    assert bidder.status_code == 200
    assert bidder.json()["gstin"] == "29ABCDE1234F1Z5"


def test_compliance_evaluation_api_returns_complete_workflow():
    client = _client()

    response = client.post(
        "/api/v1/compliance/evaluate",
        json={
            "tender_id": "TND-001",
            "bidder_id": "BIDDER-001",
            "evaluated_at": RUN_AT.isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["FAIL"] == 1
    assert payload["summary"] == {"FAIL": 1, "PASS": 4, "MANUAL_REVIEW": 13}
    assert payload["compliance_results"]
    assert payload["evidence_chains"]
    assert payload["audit_events"]

    turnover = next(
        item for item in payload["compliance_results"] if item["requirement_id"] == "REQ-TND-001-001"
    )
    assert turnover["rule_id"] == "RULE-TURNOVER-GTE"
    assert turnover["actual"] == 48_000_000

    result_id = turnover["id"]
    result = client.get(f"/api/v1/compliance/results/{result_id}")
    assert result.status_code == 200
    assert result.json()["result"]["id"] == result_id
    assert result.json()["evidence_chain"]["requirement"]["id"] == "REQ-TND-001-001"


def test_evidence_and_chain_api_after_evaluation():
    client = _client()
    report = client.post(
        "/api/v1/compliance/evaluate",
        json={"tender_id": "TND-001", "bidder_id": "BIDDER-001"},
    ).json()

    evidence_id = next(
        item["id"]
        for item in report["evidence"]
        if item["field_name"] == "average_annual_turnover"
        and item["document_id"] == "DOC-001"
    )

    evidence = client.get(f"/api/v1/evidence/{evidence_id}")
    assert evidence.status_code == 200
    assert evidence.json()["document_id"] == "DOC-001"
    assert evidence.json()["page"] == 12

    verifications = client.get(f"/api/v1/evidence/{evidence_id}/verifications")
    assert verifications.status_code == 200
    assert any(item["status"] == "VERIFIED" for item in verifications.json()["verifications"])

    chain = client.get(f"/api/v1/evidence/{evidence_id}/chain")
    assert chain.status_code == 200
    assert chain.json()["evidence_chain"]["compliance"]["status"] == "FAIL"


def test_verification_boundary_is_idempotent_for_same_mock_source():
    client = _client()
    report = client.post(
        "/api/v1/compliance/evaluate",
        json={"tender_id": "TND-001", "bidder_id": "BIDDER-001"},
    ).json()
    gst_evidence_id = next(
        item["id"] for item in report["evidence"] if item["field_name"] == "gst_status"
    )

    request = {
        "kind": "gst",
        "subject": "29ABCDE1234F1Z5",
        "evidence_id": gst_evidence_id,
        "checked_at": RUN_AT.isoformat(),
    }
    first = client.post("/api/v1/verification/verify", json=request)
    second = client.post("/api/v1/verification/verify", json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_not_found_and_bad_verification_are_clean_http_errors():
    client = _client()

    assert client.get("/api/v1/tenders/UNKNOWN").status_code == 404
    assert client.get("/api/v1/evidence/EVD-999").status_code == 404

    response = client.post(
        "/api/v1/verification/verify",
        json={
            "kind": "gst",
            "subject": "29ABCDE1234F1Z5",
            "evidence_id": "EVD-999",
        },
    )
    assert response.status_code == 400


def test_passport_verification_extraction_and_officer_audit_routes():
    client = _client()

    passport = client.get('/api/v1/bidders/BIDDER-001/passport')
    assert passport.status_code == 200
    payload = passport.json()
    assert payload['bidder']['legal_name'] == 'ABC Technologies Pvt Ltd'
    assert payload['financial_summary']['verified_turnover'] == 48_000_000
    assert payload['verification_mode'] == 'mock'

    verified = client.post('/api/v1/bidders/BIDDER-001/verify')
    assert verified.status_code == 200
    assert verified.json()['source'] == 'MOCK_VERIFICATION_ONLY'
    assert len(verified.json()['verifications']) == 4

    extraction = client.post('/api/v1/tenders/TND-001/extract')
    assert extraction.status_code == 200
    assert extraction.json()['ai_used'] is False
    assert len(extraction.json()['requirements']) == 18
    assert extraction.json()['requirements'][0]['source_page'] == 6

    eval_response = client.post(
        '/api/v1/compliance/evaluate',
        json={'tender_id': 'TND-001', 'bidder_id': 'BIDDER-001', 'evaluated_at': RUN_AT.isoformat()},
    )
    turnover = next(item for item in eval_response.json()['compliance_results'] if item['requirement_id'] == 'REQ-TND-001-001')

    commit = client.post(
        '/api/v1/audit/commit',
        json={
            'tender_id': 'TND-001',
            'bidder_id': 'BIDDER-001',
            'disposition': 'clarification',
            'note': 'Review the turnover discrepancy and supporting evidence.',
        },
    )
    assert commit.status_code == 200
    assert commit.json()['audit_event']['sha256_hash'].startswith('SHA256:')

    trail = client.get('/api/v1/audit/TND-001/BIDDER-001')
    assert trail.status_code == 200
    assert any(item['id'] == commit.json()['audit_event']['id'] for item in trail.json()['audit_events'])


def test_officer_ai_endpoints_are_factual_without_llm_key(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    client = _client()
    report = client.post(
        '/api/v1/compliance/evaluate',
        json={'tender_id': 'TND-001', 'bidder_id': 'BIDDER-001'},
    ).json()
    turnover = next(item for item in report['compliance_results'] if item['requirement_id'] == 'REQ-TND-001-001')

    explanation = client.post('/api/v1/ai/explain-contradiction', json={'result_id': turnover['id']})
    assert explanation.status_code == 200
    assert '6.20 Crore' in explanation.json()['explanation']
    assert '4.80 Crore' in explanation.json()['explanation']
    assert 'fraud' in explanation.json()['explanation'].lower() or 'does not label' in explanation.json()['explanation'].lower()

    draft = client.post(
        '/api/v1/ai/draft-clarification',
        json={
            'tender_ref': 'NPIA/EDU-ICT/2026/014',
            'bidder_name': 'ABC Technologies Pvt Ltd',
            'variance': '₹1.40 Crore',
        },
    )
    assert draft.status_code == 200
    assert 'Clarification request' in draft.json()['draft']
