from datetime import datetime, timezone
from pathlib import Path

from app.models.domain import (
    ComplianceStatus,
    TenderRequirement,
)
from app.rules.turnover import evaluate_turnover_requirement
from app.services.seed_loader import load_all_fixtures


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"


def test_all_seed_fixtures_validate():
    loaded = load_all_fixtures(FIXTURES)

    assert len(loaded["tenders.json"]) == 2
    assert len(loaded["requirements.json"]) == 36
    assert len(loaded["bidders.json"]) == 1
    assert len(loaded["documents.json"]) == 6
    assert len(loaded["evidence.json"]) == 11
    assert len(loaded["verifications.json"]) == 7
    assert len(loaded["rules.json"]) == 9


def test_tender_a_turnover_fails():
    loaded = load_all_fixtures(FIXTURES)
    requirements = loaded["requirements.json"]
    evidence = loaded["evidence.json"]
    verifications = loaded["verifications.json"]

    req = next(r for r in requirements if r.id == "REQ-TND-001-001")

    result = evaluate_turnover_requirement(
        req,
        evidence,
        verifications,
        bidder_id="BIDDER-001",
        result_id="TEST-CMP-A",
        evaluated_at=datetime(2026, 9, 17, 9, 12, tzinfo=timezone.utc),
        finding_ids=["FND-001"],
    )

    assert result.status is ComplianceStatus.FAIL
    assert result.actual == 48000000
    assert result.expected == 50000000
    assert result.evidence_ids == ["EVD-012"]
    assert result.finding_ids == ["FND-001"]


def test_tender_b_turnover_passes():
    loaded = load_all_fixtures(FIXTURES)
    requirements = loaded["requirements.json"]
    evidence = loaded["evidence.json"]
    verifications = loaded["verifications.json"]

    req = next(r for r in requirements if r.id == "REQ-TND-002-001")

    result = evaluate_turnover_requirement(
        req,
        evidence,
        verifications,
        bidder_id="BIDDER-001",
        result_id="TEST-CMP-B",
    )

    assert result.status is ComplianceStatus.PASS
    assert result.actual == 48000000
    assert result.expected == 45000000


def test_missing_verified_turnover_is_unverifiable():
    req = TenderRequirement(
        id="REQ-TEST",
        tender_id="TND-TEST",
        type="TURNOVER",
        title="Minimum Average Annual Turnover",
        description="Bidder must have average annual turnover of at least INR 5 crore.",
        operator="GREATER_THAN_OR_EQUAL",
        threshold=50000000,
        unit="INR",
        mandatory=True,
        source_document_id="DOC-TEST",
        source_page=1,
        confidence=0.96,
        rule_id="RULE-TURNOVER-GTE",
    )

    result = evaluate_turnover_requirement(
        req,
        evidence=[],
        verifications=[],
        bidder_id="BIDDER-001",
        result_id="TEST-CMP-MISSING",
    )

    assert result.status is ComplianceStatus.UNVERIFIABLE
    assert result.actual is None
    assert result.evidence_ids == []


def test_self_declared_turnover_does_not_override_verified_turnover():
    loaded = load_all_fixtures(FIXTURES)
    req = next(r for r in loaded["requirements.json"] if r.id == "REQ-TND-001-001")

    result = evaluate_turnover_requirement(
        req,
        loaded["evidence.json"],
        loaded["verifications.json"],
        bidder_id="BIDDER-001",
        result_id="TEST-CMP-CONTRADICTION",
    )

    assert result.actual == 48000000
    assert result.status is ComplianceStatus.FAIL
    assert "EVD-011" not in result.evidence_ids
