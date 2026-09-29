"""Tender requirement extraction: page-aware document text -> bounded LLM -> candidates."""

from __future__ import annotations

import ast
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

# Groq's current on-demand limit observed during testing is 8k TPM.
# Keep the request comfortably below that limit.
MAX_INPUT_CHARS = 10000
MAX_OUTPUT_TOKENS = 3000

_PAGE_MARKER_RE = re.compile(r"===== PAGE (\d+) =====")
_SERIALIZED_TEXT_RE = re.compile(r"'text': ('.*?')", re.DOTALL)

RELEVANCE_RE = re.compile(
    r"\b("
    r"eligib|qualification|qualif|requirement|mandatory|minimum|"
    r"turnover|gst|pan|udyam|msme|oem|authorization|experience|"
    r"local content|make in india|debar|blacklist|certificate|"
    r"technical specification|financial|bidder|documentary evidence|"
    r"submission|compliance|warranty|net worth|project"
    r")\b",
    re.IGNORECASE,
)


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

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


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
        raise RequirementExtractionError(
            "Every extracted requirement must be a JSON object."
        )

    return parsed


def _decode_serialized_text(value: str) -> str:
    try:
        decoded = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("'")
    return str(decoded)


def _split_embedded_page_markers(text: str) -> list[PageText]:
    """Split synthetic plain-text fixtures that already contain page markers."""
    matches = list(_PAGE_MARKER_RE.finditer(text))
    if not matches:
        return [PageText(page=1, text=text)]

    pages: list[PageText] = []

    preamble = text[: matches[0].start()].strip()
    if preamble:
        pages.append(PageText(page=1, text=preamble))

    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_page = text[start:end].strip()

        # The bundled synthetic tender fixtures contain repr()-style
        # ReportLab Paragraph objects. Extract their real text payloads so
        # those implementation details do not consume the LLM context.
        serialized_values = [
            _decode_serialized_text(m.group(1))
            for m in _SERIALIZED_TEXT_RE.finditer(raw_page)
        ]

        if serialized_values:
            cleaned = "\n".join(value.strip() for value in serialized_values if value.strip())
        else:
            cleaned = raw_page

        pages.append(PageText(page=page_number, text=cleaned))

    return pages


def _normalize_page_objects(
    tender_text: str,
    page_objects: Sequence[PageText],
) -> list[PageText]:
    """Normalize real PDF pages and synthetic marker-based text fixtures."""
    pages = list(page_objects)

    # pages_from_text() intentionally treats arbitrary text as one page.
    # Our synthetic tender fixtures, however, already contain explicit
    # ===== PAGE N ===== boundaries, so recover those boundaries here.
    if len(pages) == 1:
        source_text = str(getattr(pages[0], "text", "") or "")
        if _PAGE_MARKER_RE.search(source_text):
            return _split_embedded_page_markers(source_text)

    return pages


def _select_relevant_pages(
    page_objects: Sequence[PageText],
) -> list[PageText]:
    """Select high-signal pages while keeping the LLM request bounded."""
    pages = list(page_objects)

    scored: list[tuple[int, int, PageText]] = []
    for index, page in enumerate(pages):
        text = str(getattr(page, "text", "") or "")
        score = len(RELEVANCE_RE.findall(text))

        if index < 2:
            score += 4

        scored.append((score, index, page))

    scored.sort(key=lambda item: (-item[0], item[1]))

    selected: list[PageText] = []
    used_chars = 0

    for _, _, page in scored:
        text = str(getattr(page, "text", "") or "").strip()
        if not text:
            continue

        remaining = MAX_INPUT_CHARS - used_chars
        if remaining <= 0:
            break

        if len(text) > remaining:
            text = text[:remaining]

        selected.append(
            PageText(
                page=int(getattr(page, "page")),
                text=text,
            )
        )
        used_chars += len(text)

    if not selected:
        raise RequirementExtractionError(
            "No usable document text was available for requirement extraction."
        )

    selected.sort(key=lambda page: int(getattr(page, "page")))
    return selected


def extract_requirements(
    tender_id: str,
    tender_text: str,
    *,
    model: str = DEFAULT_MODEL,
    pages: Sequence[PageText] | None = None,
) -> RequirementExtractionResult:
    """Extract tender requirements with a bounded, page-aware LLM request."""
    if not tender_text.strip() and not pages:
        raise RequirementExtractionError(
            "Tender document contains no text to extract."
        )

    if pages is None:
        page_objects = pages_from_text(tender_text)
    else:
        page_objects = list(pages)

    page_objects = _normalize_page_objects(tender_text, page_objects)

    if not page_objects:
        raise RequirementExtractionError(
            "No document pages were supplied for extraction."
        )

    selected_pages = _select_relevant_pages(page_objects)
    page_numbers = {
        int(getattr(page, "page")) for page in selected_pages
    }
    pages_text = format_pages_for_llm(selected_pages)
    client = _client()

    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort="low",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(tender_id, pages_text),
            },
        ],
    )

    raw_text = response.choices[0].message.content or ""
    if not raw_text.strip():
        raise RequirementExtractionError(
            "The LLM returned no visible content. The request may have exhausted "
            "its completion budget on reasoning tokens; retry with the configured "
            "low reasoning effort or reduce the document context."
        )

    parsed = _parse_json_array(raw_text)

    requirements: list[ExtractedRequirementCandidate] = []
    errors: list[str] = []

    for index, item in enumerate(parsed, start=1):
        try:
            candidate = ExtractedRequirementCandidate.model_validate(item)

            if candidate.source_page not in page_numbers:
                raise ValueError(
                    f"source_page={candidate.source_page} is not present "
                    "in supplied document pages"
                )

            requirements.append(candidate)

        except (TypeError, ValueError) as exc:
            errors.append(f"item {index}: {exc}")

    if errors:
        raise RequirementExtractionError(
            "Requirement extraction produced invalid items; nothing was "
            "silently dropped:\n" + "\n".join(errors)
        )

    return RequirementExtractionResult(
        tender_id=tender_id,
        requirements=requirements,
        raw_model_output=raw_text,
    )
