from pathlib import Path

import fitz

from ai.extraction.contradiction_detector import detect_contradictions
from ai.extraction.explanation_generator import (
    _build_user_prompt,
    compliance_result_to_input,
)
from ai.extraction.field_extractor import _normalise_turnover
from ai.extraction.pdf_reader import extract_pages_from_pdf, format_pages_for_llm
from ai.schemas.models import (
    ComplianceStatus,
    ExtractedField,
    Operator,
)


def test_pdf_reader_preserves_page_numbers(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Tender requirement text with enough characters for digital extraction.")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "GST registration must be active and valid for the bidder.")
    doc.save(pdf_path)
    doc.close()

    pages = extract_pages_from_pdf(pdf_path)
    assert [page.page for page in pages] == [1, 2]
    rendered = format_pages_for_llm(pages)
    assert "===== PAGE 1 =====" in rendered
    assert "===== PAGE 2 =====" in rendered


def test_turnover_normalization():
    assert _normalise_turnover(4.8, "Crores", "Average annual turnover: Rs. 4.8 Crores") == 48_000_000.0
    assert _normalise_turnover(48_000_000, "INR", "₹48,000,000") == 48_000_000.0


def test_contradiction_detector_flags_different_turnover_values():
    fields = [
        ExtractedField(
            id="FIELD-A",
            document_id="DOC-DECL",
            field_name="average_annual_turnover",
            value=62_000_000,
            unit="INR",
            normalized_value=62_000_000,
            raw_text="Average annual turnover: Rs. 6.2 Crores",
            page=2,
            confidence=0.98,
            extraction_method="AI",
        ),
        ExtractedField(
            id="FIELD-B",
            document_id="DOC-AUDIT",
            field_name="average_annual_turnover",
            value=48_000_000,
            unit="INR",
            normalized_value=48_000_000,
            raw_text="Average annual turnover: Rs. 4.8 Crores",
            page=12,
            confidence=0.98,
            extraction_method="AI",
        ),
    ]

    findings = detect_contradictions(
        fields,
        document_types={
            "DOC-DECL": "SELF_DECLARATION",
            "DOC-AUDIT": "AUDITED_FINANCIALS",
        },
        document_names={
            "DOC-DECL": "Self_Declaration.pdf",
            "DOC-AUDIT": "Audited_Financial_Statement.pdf",
        },
    )

    assert len(findings) == 1
    assert findings[0].requires_manual_review is True
    assert "discrepancy" in findings[0].explanation.lower()
    assert "fraud" not in findings[0].explanation.lower()


def test_explanation_adapter_uses_backend_like_values_and_mock_source():
    result = {
        "expected": 50_000_000,
        "actual": 48_000_000,
        "status": "FAIL",
        "evidence_ids": ["EVD-012"],
        "finding_ids": ["FND-001"],
    }
    requirement = {
        "title": "Minimum Average Annual Turnover",
        "operator": "GREATER_THAN_OR_EQUAL",
        "threshold": 50_000_000,
        "unit": "INR",
    }
    verification = {
        "status": "VERIFIED",
        "source_type": "MOCK_GOVERNMENT_SOURCE",
        "source_name": "Mock Financial Verification",
        "details": "Mock source confirms audited turnover value.",
    }

    context = compliance_result_to_input(
        result,
        requirement,
        verification,
        declared_value=62_000_000,
    )
    prompt = _build_user_prompt(context)

    assert context.status is ComplianceStatus.FAIL
    assert context.operator is Operator.GREATER_THAN_OR_EQUAL
    assert "MOCK_GOVERNMENT_SOURCE" in prompt
    assert "Mock Financial Verification" in prompt
    assert "62,000,000" not in prompt  # comma-free values are intentionally used
    assert "62000000" in prompt
