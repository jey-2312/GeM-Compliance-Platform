"""Convert AI extraction candidates into canonical backend requirements."""

from __future__ import annotations

from typing import Iterable

from ai.schemas.models import ExtractedRequirementCandidate, RequirementExtractionResult

from app.models.domain import TenderRequirement
from app.rules.registry import rule_id_for


def adapt_requirement_candidates(
    extraction: RequirementExtractionResult | Iterable[ExtractedRequirementCandidate],
    *,
    tender_id: str | None = None,
    source_document_id: str,
) -> list[TenderRequirement]:
    """Assign backend-owned IDs/source-document IDs/rule IDs to AI candidates."""

    if isinstance(extraction, RequirementExtractionResult):
        candidates = extraction.requirements
        target_tender_id = extraction.tender_id if tender_id is None else tender_id
    else:
        candidates = list(extraction)
        if tender_id is None:
            raise ValueError("tender_id is required when adapting a raw candidate iterable")
        target_tender_id = tender_id

    requirements: list[TenderRequirement] = []
    errors: list[str] = []

    for index, candidate in enumerate(candidates, start=1):
        try:
            rule_id = rule_id_for(candidate.type.value, candidate.operator.value)
            requirements.append(
                TenderRequirement(
                    id=f"REQ-{target_tender_id}-{index:03d}",
                    tender_id=target_tender_id,
                    type=candidate.type.value,
                    title=candidate.title,
                    description=candidate.description,
                    operator=candidate.operator.value,
                    threshold=candidate.threshold,
                    unit=candidate.unit,
                    mandatory=candidate.mandatory,
                    source_document_id=source_document_id,
                    source_page=candidate.source_page,
                    confidence=candidate.confidence,
                    rule_id=rule_id,
                )
            )
        except ValueError as exc:
            errors.append(f"candidate {index}: {exc}")

    if errors:
        raise ValueError(
            "AI requirements could not be adapted to the canonical backend contract:\n"
            + "\n".join(errors)
        )

    return requirements
