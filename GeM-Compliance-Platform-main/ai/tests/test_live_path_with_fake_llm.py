import json
from types import SimpleNamespace

import pytest

from ai.extraction import field_extractor, requirement_extractor
from ai.extraction.pdf_reader import PageText
from ai.schemas.models import RequirementType, Operator


def fake_client(payload: list[dict]):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: response)
        )
    )


def test_requirement_extractor_live_path_uses_model_page(monkeypatch):
    payload = [
        {
            "type": "TURNOVER",
            "title": "Minimum Average Annual Turnover",
            "description": "Bidder must have average annual turnover of at least INR 5 crore.",
            "operator": "GREATER_THAN_OR_EQUAL",
            "threshold": 50_000_000,
            "unit": "INR",
            "mandatory": True,
            "source_page": 7,
            "confidence": 0.96,
        }
    ]
    monkeypatch.setattr(requirement_extractor, "_client", lambda: fake_client(payload))

    result = requirement_extractor.extract_requirements(
        "TND-001",
        "",
        pages=[PageText(page=7, text="Minimum Average Annual Turnover: 5 Crore")],
    )

    assert len(result.requirements) == 1
    assert result.requirements[0].source_page == 7
    assert result.requirements[0].type is RequirementType.TURNOVER
    assert result.requirements[0].operator is Operator.GREATER_THAN_OR_EQUAL


def test_requirement_extractor_rejects_unknown_source_page(monkeypatch):
    payload = [
        {
            "type": "TURNOVER",
            "title": "Turnover",
            "description": "Minimum turnover.",
            "operator": "GREATER_THAN_OR_EQUAL",
            "threshold": 50_000_000,
            "unit": "INR",
            "mandatory": True,
            "source_page": 8,
            "confidence": 0.9,
        }
    ]
    monkeypatch.setattr(requirement_extractor, "_client", lambda: fake_client(payload))

    with pytest.raises(requirement_extractor.RequirementExtractionError, match="not present"):
        requirement_extractor.extract_requirements(
            "TND-001",
            "",
            pages=[PageText(page=7, text="Minimum turnover")],
        )


def test_field_extractor_live_path_normalizes_turnover(monkeypatch):
    payload = [
        {
            "field_name": "average_annual_turnover",
            "value": 4.8,
            "unit": "Crores",
            "normalized_value": None,
            "raw_text": "Average annual turnover: Rs. 4.8 Crores",
            "page": 12,
            "confidence": 0.98,
        }
    ]
    monkeypatch.setattr(field_extractor, "_client", lambda: fake_client(payload))

    fields = field_extractor.extract_fields(
        document_id="DOC-001",
        document_type="AUDITED_FINANCIALS",
        document_text="",
        target_fields=["average_annual_turnover"],
        pages=[PageText(page=12, text="Average annual turnover: Rs. 4.8 Crores")],
    )

    assert len(fields) == 1
    assert fields[0].id == "FIELD-DOC-001-001"
    assert fields[0].normalized_value == 48_000_000.0
    assert fields[0].page == 12


def test_field_extractor_rejects_missing_requested_field(monkeypatch):
    monkeypatch.setattr(field_extractor, "_client", lambda: fake_client([]))

    with pytest.raises(field_extractor.FieldExtractionError, match="missing requested fields"):
        field_extractor.extract_fields(
            document_id="DOC-001",
            document_type="AUDITED_FINANCIALS",
            document_text="No turnover here.",
            target_fields=["average_annual_turnover"],
        )
