"""Tender requirement extraction: page-aware document text -> LLM -> candidates."""

from __future__ import annotations

import json
import os
import re
from typing import Sequence, TYPE_CHECKING

from ai.prompts.extraction_prompt import SYSTEM_PROMPT, build_user_prompt
from ai.extraction.pdf_reader import PageText, format_pages_for_llm, pages_from_text
from ai.schemas.models import (
    ExtractedRequirementCandidate,
    RequirementExtractionResult,
)

if TYPE_CHECKING:
    from openai import OpenAI

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-20b")
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class RequirementExtractionError(ValueError):
    """Raised when the LLM returns unusable or incomplete requirement data."""


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


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


def _parse_json_array(raw_text: str) -> list[dict]:
    cleaned = _strip_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RequirementExtractionError(
            f"Model did not return valid JSON. Raw output:\n{raw_text}"
        ) from exc

    if not isinstance(parsed, list):
        raise RequirementExtractionError(
            f"Expected a JSON array, got {type(parsed).__name__}."
        )

    if not all(isinstance(item, dict) for item in parsed):
        raise RequirementExtractionError("Every extracted requirement must be a JSON object.")

    return parsed


def extract_requirements(
    tender_id: str,
    tender_text: str,
    *,
    model: str = DEFAULT_MODEL,
    pages: Sequence[PageText] | None = None,
) -> RequirementExtractionResult:
    """Extract tender requirements while preserving source page information.

    `pages` may be a sequence of `PageText` objects. For a plain text fixture,
    omit it and the text is treated as one explicit page (page 1).
    """

    if not tender_text.strip() and not pages:
        raise RequirementExtractionError("Tender document contains no text to extract.")

    if pages is None:
        page_objects = pages_from_text(tender_text)
    else:
        page_objects = list(pages)

    if not page_objects:
        raise RequirementExtractionError("No document pages were supplied for extraction.")

    page_numbers = {int(getattr(page, "page")) for page in page_objects}
    pages_text = format_pages_for_llm(page_objects)
    client = _client()

    response = client.chat.completions.create(
        model=model,
        max_tokens=2500,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(tender_id, pages_text)},
        ],
    )

    raw_text = response.choices[0].message.content or ""
    parsed = _parse_json_array(raw_text)

    requirements: list[ExtractedRequirementCandidate] = []
    errors: list[str] = []

    for index, item in enumerate(parsed, start=1):
        try:
            candidate = ExtractedRequirementCandidate.model_validate(item)
            if candidate.source_page not in page_numbers:
                raise ValueError(
                    f"source_page={candidate.source_page} is not present in supplied document pages"
                )
            requirements.append(candidate)
        except (TypeError, ValueError) as exc:
            errors.append(f"item {index}: {exc}")

    if errors:
        raise RequirementExtractionError(
            "Requirement extraction produced invalid items; nothing was silently dropped:\n"
            + "\n".join(errors)
        )

    return RequirementExtractionResult(
        tender_id=tender_id,
        requirements=requirements,
        raw_model_output=raw_text,
    )
