from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.evidence import (
    DuplicateEvidenceError,
    EvidenceEngine,
    EvidenceNotFoundError,
    EvidenceValidationError,
)
from app.models.domain import ComplianceStatus, RuleDefinition
from app.rules.turnover import evaluate_turnover_requirement
from app.services.seed_loader import load_all_fixtures
from app.verification.mock_financial import MockFinancialVerificationConnector


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"


def _loaded_engine() -> tuple[dict, EvidenceEngine]:
    loaded = load_all_fixtures(FIXTURES)
    engine = EvidenceEngine(
        evidence=loaded["evidence.json"],
        verifications=loaded["verifications.json"],
    )
    return loaded, engine


def test_create_evidence_from_extracted_field_uses_normalized_value():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = next(r for r in loaded["requirements.json"] if r.id == "REQ-001")
    document = next(d for d in loaded["documents.json"] if d.id == "DOC-001")
    field = next(f for f in loaded["extracted_fields.json"] if f.id == "FIELD-001")

    engine = EvidenceEngine()
    evidence = engine.create_from_extracted_field(
        bidder=bidder,
        requirement=requirement,
        document=document,
        extracted_field=field,
    )

    assert evidence.id == "EVD-001"
    assert evidence.requirement_id == "REQ-001"
    assert evidence.document_id == "DOC-001"
    assert evidence.page == 12
    assert evidence.field_name == "average_annual_turnover"
    assert evidence.value == 48_000_000
    assert evidence.unit == "INR"
    assert evidence.source_label == "Audited_Financial_Statement.pdf"
    assert evidence.verification_status == "UNVERIFIED"
    assert evidence.confidence == 0.98
    assert evidence.id in bidder.evidence_ids


def test_deduplication_does_not_duplicate_same_extraction():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = next(r for r in loaded["requirements.json"] if r.id == "REQ-001")
    document = next(d for d in loaded["documents.json"] if d.id == "DOC-001")
    field = next(f for f in loaded["extracted_fields.json"] if f.id == "FIELD-001")

    engine = EvidenceEngine()
    first = engine.create_from_extracted_field(
        bidder=bidder,
        requirement=requirement,
        document=document,
        extracted_field=field,
    )
    second = engine.create_from_extracted_field(
        bidder=bidder,
        requirement=requirement,
        document=document,
        extracted_field=field,
    )

    assert first.id == second.id
    assert len(engine.get_all_evidence()) == 1


def test_registered_duplicate_id_is_rejected():
    loaded, engine = _loaded_engine()
    existing = loaded["evidence.json"][0]

    with pytest.raises(DuplicateEvidenceError):
        engine.register_evidence(existing.model_copy())


def test_invalid_document_page_is_rejected():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = loaded["requirements.json"][0]
    document = loaded["documents.json"][0]
    field = loaded["extracted_fields.json"][0].model_copy(update={"page": 99})

    engine = EvidenceEngine()
    with pytest.raises(EvidenceValidationError, match="outside document page range"):
        engine.create_from_extracted_field(
            bidder=bidder,
            requirement=requirement,
            document=document,
            extracted_field=field,
        )


def test_mismatched_document_is_rejected():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = loaded["requirements.json"][0]
    document = loaded["documents.json"][1]
    field = loaded["extracted_fields.json"][0]

    engine = EvidenceEngine()
    with pytest.raises(EvidenceValidationError, match="does not match the supplied document"):
        engine.create_from_extracted_field(
            bidder=bidder,
            requirement=requirement,
            document=document,
            extracted_field=field,
        )


def test_mismatched_bidder_is_rejected():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0].model_copy(update={"id": "BIDDER-002"})
    requirement = loaded["requirements.json"][0]
    document = loaded["documents.json"][0]
    field = loaded["extracted_fields.json"][0]

    engine = EvidenceEngine()
    with pytest.raises(EvidenceValidationError, match="Document bidder does not match"):
        engine.create_from_extracted_field(
            bidder=bidder,
            requirement=requirement,
            document=document,
            extracted_field=field,
        )


def test_verification_attachment_updates_evidence_status():
    loaded, engine = _loaded_engine()
    evidence = engine.get_evidence("EVD-012")
    assert evidence.verification_status == "VERIFIED"

    verification = engine.get_verifications_for_evidence("EVD-012")
    assert len(verification) == 1
    assert verification[0].status == "VERIFIED"
    assert verification[0].verified_value == 48_000_000


def test_verification_status_tracks_latest_checked_result():
    loaded = load_all_fixtures(FIXTURES)
    engine = EvidenceEngine(evidence=loaded["evidence.json"])
    evidence = engine.get_evidence("EVD-012")

    from app.models.domain import Verification

    newer = Verification(
        id="VER-NEWER",
        evidence_id=evidence.id,
        source_type="MOCK_GOVERNMENT_SOURCE",
        source_name="Mock Financial Verification",
        checked_at=datetime(2026, 9, 18, 9, 10, tzinfo=timezone.utc),
        status="VERIFIED",
        verified_value=48_000_000,
        details="Newer verification record.",
    )
    older = Verification(
        id="VER-OLDER",
        evidence_id=evidence.id,
        source_type="MOCK_GOVERNMENT_SOURCE",
        source_name="Mock Financial Verification",
        checked_at=datetime(2026, 9, 17, 9, 10, tzinfo=timezone.utc),
        status="NOT_FOUND",
        verified_value=None,
        details="Older verification record.",
    )

    engine.attach_verification(newer)
    engine.attach_verification(older)

    assert engine.get_latest_verification(evidence.id).id == "VER-NEWER"
    assert engine.get_evidence(evidence.id).verification_status == "VERIFIED"


def test_verify_and_attach_rejects_connector_returning_wrong_evidence_id():
    loaded = load_all_fixtures(FIXTURES)
    engine = EvidenceEngine(evidence=loaded["evidence.json"])
    evidence = engine.get_evidence("EVD-012")

    class BadConnector:
        source_name = "Bad Connector"

        def verify(self, subject, *, evidence_id, checked_at=None):
            from app.models.domain import Verification

            return Verification(
                id="VER-BAD",
                evidence_id="EVD-999",
                source_type="MOCK_GOVERNMENT_SOURCE",
                source_name=self.source_name,
                checked_at=checked_at or datetime.now(timezone.utc),
                status="VERIFIED",
                verified_value=48_000_000,
                details="Invalid connector result for test.",
            )

    with pytest.raises(EvidenceValidationError, match="different evidence_id"):
        engine.verify_and_attach(
            evidence_id=evidence.id,
            subject="BIDDER-001",
            connector=BadConnector(),
        )


def test_verify_and_attach_uses_mock_financial_connector():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = next(r for r in loaded["requirements.json"] if r.id == "REQ-001")
    document = next(d for d in loaded["documents.json"] if d.id == "DOC-001")
    field = next(f for f in loaded["extracted_fields.json"] if f.id == "FIELD-001")

    engine = EvidenceEngine()
    evidence = engine.create_from_extracted_field(
        bidder=bidder,
        requirement=requirement,
        document=document,
        extracted_field=field,
    )

    verification = engine.verify_and_attach(
        evidence_id=evidence.id,
        subject=bidder.id,
        connector=MockFinancialVerificationConnector(),
        checked_at=datetime(2026, 9, 17, 9, 10, tzinfo=timezone.utc),
    )

    assert verification.evidence_id == evidence.id
    assert verification.status == "VERIFIED"
    assert verification.verified_value == 48_000_000
    assert engine.get_evidence(evidence.id).verification_status == "VERIFIED"


def test_unknown_evidence_lookup_raises():
    engine = EvidenceEngine()
    with pytest.raises(EvidenceNotFoundError):
        engine.get_evidence("EVD-999")


def test_evidence_for_requirement_is_sorted_by_page_then_id():
    loaded, engine = _loaded_engine()
    matches = engine.get_evidence_for_requirement(
        bidder_id="BIDDER-001",
        requirement_id="REQ-001",
    )

    assert [item.id for item in matches] == ["EVD-011", "EVD-012"]
    assert [item.page for item in matches] == [2, 12]


def test_evidence_chain_contains_requirement_rule_evidence_and_verification():
    loaded = load_all_fixtures(FIXTURES)
    engine = EvidenceEngine(
        evidence=loaded["evidence.json"],
        verifications=loaded["verifications.json"],
        documents=loaded["documents.json"],
        extracted_fields=loaded["extracted_fields.json"],
    )
    requirement = next(r for r in loaded["requirements.json"] if r.id == "REQ-001")
    rule = next(r for r in loaded["rules.json"] if r.id == "RULE-TURNOVER-GTE")
    compliance = next(r for r in loaded["compliance_results.json"] if r.id == "CMP-001")
    audit = next(r for r in loaded["audit_events.json"] if r.id == "AUD-001")

    chain = engine.build_evidence_chain(
        requirement=requirement,
        rule=rule,
        compliance_result=compliance,
        audit_event=audit,
    )

    assert chain["requirement"]["id"] == "REQ-001"
    assert chain["rule"]["id"] == "RULE-TURNOVER-GTE"
    assert len(chain["evidence"]) == 2
    audited = next(node for node in chain["evidence"] if node["evidence"]["id"] == "EVD-012")
    assert audited["document"]["id"] == "DOC-001"
    assert audited["page"] == 12
    assert audited["extracted_field"]["id"] == "FIELD-001"
    assert audited["extracted_field"]["raw_text"] == "Average annual turnover: Rs. 4.8 Crores"
    assert audited["extracted_value"]["value"] == 48_000_000
    assert audited["verifications"][0]["id"] == "VER-001"
    assert chain["compliance"]["status"] == "FAIL"
    assert chain["audit"]["action"] == "COMPLIANCE_EVALUATED"


def test_full_evidence_to_rule_flow_uses_verified_value():
    loaded = load_all_fixtures(FIXTURES)
    bidder = loaded["bidders.json"][0]
    requirement = next(r for r in loaded["requirements.json"] if r.id == "REQ-001")
    document = next(d for d in loaded["documents.json"] if d.id == "DOC-001")
    field = next(f for f in loaded["extracted_fields.json"] if f.id == "FIELD-001")

    engine = EvidenceEngine()
    evidence = engine.create_from_extracted_field(
        bidder=bidder,
        requirement=requirement,
        document=document,
        extracted_field=field,
    )
    engine.verify_and_attach(
        evidence_id=evidence.id,
        subject=bidder.id,
        connector=MockFinancialVerificationConnector(),
        checked_at=datetime(2026, 9, 17, 9, 10, tzinfo=timezone.utc),
    )

    result = evaluate_turnover_requirement(
        requirement,
        engine.get_all_evidence(),
        engine.get_all_verifications(),
        bidder_id=bidder.id,
        result_id="CMP-EVIDENCE-INTEGRATION",
    )

    assert result.status is ComplianceStatus.FAIL
    assert result.actual == 48_000_000
    assert result.evidence_ids == [evidence.id]
