"""Officer-facing explanation generation from deterministic compliance results."""

from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

from ai.schemas.models import ComplianceResultInput, Operator, ComplianceStatus

if TYPE_CHECKING:
    from openai import OpenAI

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-20b")

SYSTEM_PROMPT = """You write short, neutral explanations for a procurement officer reviewing AI-assisted bid compliance results. The compliance status has ALREADY been determined by deterministic backend code. You only explain the supplied result.

Hard rules:
- Never imply that the AI made the compliance decision.
- Never say that a discrepancy proves fraud or collusion. Call it a discrepancy or contradiction requiring review.
- Never claim a live government connection when the source is mocked. Describe the verification source exactly as supplied.
- Do not change PASS, FAIL, MANUAL_REVIEW, PENDING, UNVERIFIABLE, or NOT_APPLICABLE.
- Do not invent values, evidence, verification sources, or reasons.
- One or two factual sentences maximum.
- Output ONLY the explanation text; no quotes, markdown, or preamble."""


def _client() -> "OpenAI":
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The AI dependencies are not installed. Run: "
            "python -m pip install -r ai/requirements.txt"
        ) from exc

    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Copy .env.example to .env and fill it "
            "with an authorized Groq API key."
        )
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def compliance_result_to_input(
    result: Any,
    requirement: Any,
    verification: Any | None = None,
    *,
    declared_value: Any | None = None,
) -> ComplianceResultInput:
    """Adapt the real backend ComplianceResult into the AI explanation schema.

    `result`, `requirement`, and `verification` can be backend Pydantic models
    or ordinary dictionaries. This keeps the AI package from owning a second
    ComplianceResult domain model.
    """

    def get(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    operator_value = get(requirement, "operator")
    if hasattr(operator_value, "value"):
        operator_value = operator_value.value
    operator = operator_value if isinstance(operator_value, Operator) else Operator(str(operator_value))

    status_value = get(result, "status")
    if hasattr(status_value, "value"):
        status_value = status_value.value
    status = status_value if isinstance(status_value, ComplianceStatus) else ComplianceStatus(str(status_value))

    return ComplianceResultInput(
        requirement_title=str(get(requirement, "title", "")),
        operator=operator,
        threshold=get(result, "expected", get(requirement, "threshold")),
        unit=get(requirement, "unit"),
        actual=get(result, "actual"),
        status=status,
        evidence_ids=list(get(result, "evidence_ids", []) or []),
        finding_ids=list(get(result, "finding_ids", []) or []),
        verification_status=get(verification, "status") if verification is not None else None,
        verification_source_type=get(verification, "source_type") if verification is not None else None,
        verification_source_name=get(verification, "source_name") if verification is not None else None,
        verification_details=get(verification, "details") if verification is not None else None,
        declared_value=declared_value,
    )


def _build_user_prompt(result: ComplianceResultInput) -> str:
    lines = [
        f"Requirement: {result.requirement_title}",
        f"Operator: {result.operator.value}",
        f"Threshold: {result.threshold} {result.unit or ''}".strip(),
        f"Actual value: {result.actual}",
        f"Compliance status: {result.status.value}",
        f"Evidence IDs: {', '.join(result.evidence_ids) if result.evidence_ids else 'none'}",
        f"Finding IDs: {', '.join(result.finding_ids) if result.finding_ids else 'none'}",
    ]

    if result.verification_status:
        lines.append(f"Verification status: {result.verification_status}")
    if result.verification_source_type:
        lines.append(f"Verification source type: {result.verification_source_type}")
    if result.verification_source_name:
        lines.append(f"Verification source name: {result.verification_source_name}")
    if result.verification_details:
        lines.append(f"Verification details: {result.verification_details}")
    if result.declared_value is not None and result.declared_value != result.actual:
        lines.append(
            f"Self-declared value: {result.declared_value}; it differs from the supplied actual/verified value."
        )

    lines.append("Write one or two sentences explaining only these supplied facts.")
    return "\n".join(lines)


def generate_explanation(
    result: ComplianceResultInput,
    model: str = DEFAULT_MODEL,
) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        max_tokens=500,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(result)},
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("Explanation model returned empty output.")
    return text.strip('"')


def generate_explanation_from_result(
    result: Any,
    requirement: Any,
    verification: Any | None = None,
    *,
    declared_value: Any | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate an explanation directly from the actual backend result."""

    context = compliance_result_to_input(
        result,
        requirement,
        verification,
        declared_value=declared_value,
    )
    return generate_explanation(context, model=model)
