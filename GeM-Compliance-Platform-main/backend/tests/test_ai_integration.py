import json
from pathlib import Path

import pytest

from ai.extraction.requirement_extractor import RequirementExtractionError
from ai.prompts.extraction_prompt import build_user_prompt
from ai.schemas.models import (
    ComplianceStatus,
    ExtractedRequirementCandidate,
    Operator,
    RequirementExtractionResult,
    RequirementType,
)
from app.models.domain import TenderRequirement
from app.services.requirement_adapter import adapt_requirement_candidates


FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"


def test_ai_candidate_to_backend_requirement_contract():
    candidate = ExtractedRequirementCandidate(
        type=RequirementType.TURNOVER,
        title="Minimum Average Annual Turnover",
        description="Bidder must have average annual turnover of at least INR 5 crore.",
        operator=Operator.GREATER_THAN_OR_EQUAL,
        threshold=50_000_000,
        unit="INR",
        mandatory=True,
        source_page=6,
        confidence=0.96,
    )
    result = RequirementExtractionResult(tender_id="TND-001", requirements=[candidate])

    adapted = adapt_requirement_candidates(result, source_document_id="DOC-TENDER-001")

    assert len(adapted) == 1
    domain_req = TenderRequirement.model_validate(adapted[0].model_dump())
    assert domain_req.id == "REQ-TND-001-001"
    assert domain_req.source_document_id == "DOC-TENDER-001"
    assert domain_req.source_page == 6
    assert domain_req.rule_id == "RULE-TURNOVER-GTE"


def test_requirement_ids_do_not_collide_between_tenders():
    candidate = ExtractedRequirementCandidate(
        type=RequirementType.TURNOVER,
        title="Turnover",
        description="Minimum turnover.",
        operator=Operator.GREATER_THAN_OR_EQUAL,
        threshold=50_000_000,
        unit="INR",
        mandatory=True,
        source_page=1,
        confidence=0.9,
    )

    a = adapt_requirement_candidates(
        RequirementExtractionResult(tender_id="TND-001", requirements=[candidate]),
        source_document_id="DOC-A",
    )
    b = adapt_requirement_candidates(
        RequirementExtractionResult(tender_id="TND-002", requirements=[candidate]),
        source_document_id="DOC-B",
    )

    assert a[0].id != b[0].id


def test_rule_id_is_backend_owned_and_canonical():
    candidate = ExtractedRequirementCandidate(
        type=RequirementType.TURNOVER,
        title="Turnover",
        description="Minimum turnover.",
        operator=Operator.GREATER_THAN_OR_EQUAL,
        threshold=50_000_000,
        unit="INR",
        mandatory=True,
        source_page=2,
        confidence=0.9,
    )
    result = adapt_requirement_candidates(
        RequirementExtractionResult(tender_id="TND-001", requirements=[candidate]),
        source_document_id="DOC-TENDER-001",
    )[0]
    assert result.rule_id == "RULE-TURNOVER-GTE"


def test_unsupported_rule_is_not_invented():
    candidate = ExtractedRequirementCandidate(
        type=RequirementType.OTHER,
        title="Unsupported",
        description="No backend rule yet.",
        operator=Operator.EQUAL,
        threshold=None,
        unit=None,
        mandatory=True,
        source_page=1,
        confidence=0.8,
    )
    with pytest.raises(ValueError, match="No canonical rule"):
        adapt_requirement_candidates(
            RequirementExtractionResult(tender_id="TND-001", requirements=[candidate]),
            source_document_id="DOC-TENDER-001",
        )


def test_invalid_llm_item_is_not_silently_dropped(monkeypatch):
    from types import SimpleNamespace
    from ai.extraction import requirement_extractor as extractor

    bad_item = {
        "type": "TURNOVER",
        "title": "Turnover",
        "description": "Minimum turnover",
        "operator": "GREATER_THAN_OR_EQUAL",
        "threshold": 50_000_000,
        "unit": "INR",
        "mandatory": True,
        "source_page": 0,
        "confidence": 0.9,
    }

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps([bad_item])))]
    )
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: fake_response))
    )
    monkeypatch.setattr(extractor, "_client", lambda: fake_client)

    with pytest.raises(RequirementExtractionError, match="invalid items"):
        extractor.extract_requirements(
            "TND-001",
            "Minimum turnover 5 Cr",
        )


def test_prompt_preserves_page_and_untrusted_data_rules():
    prompt = build_user_prompt("TND-001", "===== PAGE 6 =====\nMinimum turnover 5 Cr")
    assert "PAGE 6" in prompt
    assert "TND-001" in prompt


def test_explanation_adapter_accepts_actual_backend_models():
    from ai.extraction.explanation_generator import compliance_result_to_input
    from app.models.domain import ComplianceResult, Verification

    requirement = TenderRequirement(
        id="REQ-TND-001-001",
        tender_id="TND-001",
        type="TURNOVER",
        title="Minimum Average Annual Turnover",
        description="Minimum turnover.",
        operator="GREATER_THAN_OR_EQUAL",
        threshold=50_000_000,
        unit="INR",
        mandatory=True,
        source_document_id="DOC-TENDER-001",
        source_page=6,
        confidence=0.96,
        rule_id="RULE-TURNOVER-GTE",
    )
    result = ComplianceResult(
        id="CMP-001",
        tender_id="TND-001",
        bidder_id="BIDDER-001",
        requirement_id="REQ-TND-001-001",
        status="FAIL",
        rule_id="RULE-TURNOVER-GTE",
        expected=50_000_000,
        actual=48_000_000,
        evidence_ids=["EVD-012"],
        finding_ids=["FND-001"],
        explanation="Verified turnover is below the tender threshold.",
        evaluated_at="2026-09-17T09:12:00+00:00",
    )
    verification = Verification(
        id="VER-001",
        evidence_id="EVD-012",
        source_type="MOCK_GOVERNMENT_SOURCE",
        source_name="Mock Financial Verification",
        checked_at="2026-09-17T09:10:00+00:00",
        status="VERIFIED",
        verified_value=48_000_000,
        details="Mock source confirms audited turnover value.",
    )

    context = compliance_result_to_input(result, requirement, verification, declared_value=62_000_000)

    assert context.status is ComplianceStatus.FAIL
    assert context.actual == 48_000_000
    assert context.verification_source_name == "Mock Financial Verification"
    assert context.declared_value == 62_000_000


def test_ai_candidate_flows_into_turnover_rule():
    from app.rules.turnover import evaluate_turnover_requirement
    from app.models.domain import ComplianceStatus as BackendComplianceStatus, Evidence, Verification

    candidate = ExtractedRequirementCandidate(
        type=RequirementType.TURNOVER,
        title="Minimum Average Annual Turnover",
        description="Bidder must have average annual turnover of at least INR 5 crore.",
        operator=Operator.GREATER_THAN_OR_EQUAL,
        threshold=50_000_000,
        unit="INR",
        mandatory=True,
        source_page=6,
        confidence=0.96,
    )
    requirement = adapt_requirement_candidates(
        RequirementExtractionResult(tender_id="TND-001", requirements=[candidate]),
        source_document_id="DOC-TENDER-001",
    )[0]
    evidence = Evidence(
        id="EVD-012",
        bidder_id="BIDDER-001",
        requirement_id=requirement.id,
        document_id="DOC-001",
        page=12,
        evidence_type="DOCUMENT_EXTRACT",
        field_name="average_annual_turnover",
        value=48_000_000,
        unit="INR",
        source_label="Audited Financial Statement",
        confidence=0.98,
        verification_status="VERIFIED",
        notes="Audited value.",
    )
    verification = Verification(
        id="VER-001",
        evidence_id="EVD-012",
        source_type="MOCK_GOVERNMENT_SOURCE",
        source_name="Mock Financial Verification",
        checked_at="2026-09-17T09:10:00+00:00",
        status="VERIFIED",
        verified_value=48_000_000,
        details="Mock source confirms audited turnover value.",
    )

    result = evaluate_turnover_requirement(
        requirement,
        [evidence],
        [verification],
        bidder_id="BIDDER-001",
        result_id="CMP-AI-INTEGRATION",
    )

    assert result.status is BackendComplianceStatus.FAIL
    assert result.actual == 48_000_000
    assert result.evidence_ids == ["EVD-012"]
    assert result.rule_id == "RULE-TURNOVER-GTE"
