# AI Workstream

The AI workstream performs document understanding and explanation only.

## Flow

`Tender/Bidder document -> page-aware text -> LLM extraction -> validated candidate -> backend canonical adapter -> deterministic rule/evidence pipeline`

The LLM does not assign canonical entity IDs, rule IDs, or PASS/FAIL decisions.

## Requirement extraction

```python
from ai.extraction.requirement_extractor import extract_requirements

result = extract_requirements(
    tender_id="TND-001",
    tender_text=text,
    pages=pages,
)
```

The result contains `ExtractedRequirementCandidate` objects with source pages.
The backend adapter assigns `REQ-*`, source document IDs and canonical rule IDs.

## Bidder field extraction

```python
from ai.extraction.field_extractor import extract_fields

fields = extract_fields(
    document_id="DOC-001",
    document_type="AUDITED_FINANCIALS",
    document_text=text,
    target_fields=["average_annual_turnover"],
    pages=pages,
)
```

## Contradictions

`ai/extraction/contradiction_detector.py` performs a narrow evidence cross-check.
It reports discrepancies for manual review and never declares fraud or collusion.

## Explanation

`generate_explanation_from_result()` accepts the actual backend
`ComplianceResult` shape plus its requirement and optional verification metadata.
The LLM explains the already-determined status; it does not decide it.

## Dependencies

```bash
python -m pip install -r ai/requirements.txt
python -m pip install -r ai/requirements-dev.txt
```
