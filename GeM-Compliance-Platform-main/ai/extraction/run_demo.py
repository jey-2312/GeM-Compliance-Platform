"""Run the AI workstream demo from the repository root.

Live mode (requires LLM_API_KEY):
    python -m ai.extraction.run_demo --live

Offline mode uses frozen, corrected requirement fixtures and the real backend
rule engine for the explanation adapter test:
    python -m ai.extraction.run_demo --offline

The demo never treats mock verification as a live government integration.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.extraction.contradiction_detector import detect_contradictions  # noqa: E402
from ai.extraction.explanation_generator import (  # noqa: E402
    generate_explanation_from_result,
)
from ai.extraction.field_extractor import extract_fields  # noqa: E402
from ai.extraction.pdf_reader import pages_from_text  # noqa: E402
from ai.extraction.requirement_extractor import extract_requirements  # noqa: E402
from ai.schemas.models import ExtractedField, TenderRequirement  # noqa: E402
from app.models.domain import Evidence, TenderRequirement as BackendTenderRequirement, Verification  # noqa: E402
from app.rules.turnover import evaluate_turnover_requirement  # noqa: E402
from app.services.requirement_adapter import adapt_requirement_candidates  # noqa: E402


def _load_json(name: str):
    return json.loads((FIXTURES_DIR / name).read_text())


def run_requirement_demo(live: bool) -> None:
    print("=" * 70)
    print("STEP 1 — Requirement extraction")
    print("=" * 70)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    tender_inputs = [
        ("TND-001", "DOC-TENDER-001", "tender_a.txt", "TND-001_requirements.json"),
        ("TND-002", "DOC-TENDER-002", "tender_b.txt", "TND-002_requirements.json"),
    ]

    for tender_id, document_id, filename, output_name in tender_inputs:
        text = (REPO_ROOT / "data" / "tenders" / filename).read_text()
        if live:
            candidates = extract_requirements(
                tender_id=tender_id,
                tender_text=text,
                pages=pages_from_text(text),
            )
            canonical = adapt_requirement_candidates(
                candidates,
                source_document_id=document_id,
            )
            data = [item.model_dump(mode="json") for item in canonical]
        else:
            data = _load_json(output_name)
            [BackendTenderRequirement.model_validate(item) for item in data]

        (FIXTURES_DIR / output_name).write_text(json.dumps(data, indent=2))
        print(f"{tender_id}: {len(data)} canonical requirements -> {output_name}")
        for item in data:
            print(
                f"  {item['id']} [{item['type']}] page={item['source_page']} "
                f"rule={item['rule_id']}"
            )


def run_field_and_contradiction_demo(live: bool) -> None:
    print("\n" + "=" * 70)
    print("STEP 2 — Bidder field extraction and contradiction check")
    print("=" * 70)

    if live:
        print("Live field extraction is available through ai.extraction.field_extractor.extract_fields().")
        print("The demo uses the frozen seed fields so it does not require bidder PDFs to be present.")

    field_data = _load_json("extracted_fields.json")
    fields = [ExtractedField.model_validate(item) for item in field_data]
    documents = {item["id"]: item for item in _load_json("documents.json")}
    findings = detect_contradictions(
        fields,
        document_types={doc_id: item["document_type"] for doc_id, item in documents.items()},
        document_names={doc_id: item["name"] for doc_id, item in documents.items()},
    )

    print(f"Extracted fields loaded: {len(fields)}")
    print(f"Contradictions found: {len(findings)}")
    for finding in findings:
        print(f"  {finding.finding_id}: {finding.explanation}")


def run_explanation_demo() -> None:
    print("\n" + "=" * 70)
    print("STEP 3 — Explanation generation from the real backend result")
    print("=" * 70)

    requirements = [BackendTenderRequirement.model_validate(item) for item in _load_json("requirements.json")]
    evidence = [Evidence.model_validate(item) for item in _load_json("evidence.json")]
    verifications = [Verification.model_validate(item) for item in _load_json("verifications.json")]

    req = next(req for req in requirements if req.id == "REQ-TND-001-001")
    result = evaluate_turnover_requirement(
        req,
        evidence,
        verifications,
        bidder_id="BIDDER-001",
        result_id="DEMO-CMP-001",
    )
    verification = next(
        item for item in verifications if item.evidence_id in result.evidence_ids
    )

    if not os.environ.get("LLM_API_KEY"):
        print("No LLM_API_KEY set; skipping live explanation call.")
        print(f"Backend result is {result.status.value}; explanation adapter is ready.")
        return

    explanation = generate_explanation_from_result(
        result,
        req,
        verification,
        declared_value=62_000_000,
    )
    print(f"{result.status.value}: {explanation}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Call the configured LLM API.")
    parser.add_argument("--offline", action="store_true", help="Use frozen local fixtures.")
    args = parser.parse_args()

    if args.live and args.offline:
        parser.error("Choose either --live or --offline, not both.")

    live = args.live
    if not live and os.environ.get("LLM_API_KEY") and not args.offline:
        live = True

    run_requirement_demo(live=live)
    run_field_and_contradiction_demo(live=live)
    run_explanation_demo()
    print("\nAI workstream demo complete.")


if __name__ == "__main__":
    main()
