"""Evidence discrepancy detection for the prototype.

This module performs a narrow deterministic cross-check on extracted fields.
It identifies conflicting values but never labels a bidder as fraudulent or
makes a compliance decision.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

from ai.schemas.models import ContradictionFinding, ExtractedField


def _source_label(document_type: str, document_name: str) -> str:
    known = {
        "SELF_DECLARATION": "Self Declaration",
        "AUDITED_FINANCIALS": "Audited Financial Statement",
        "GST_CERTIFICATE": "GST Certificate",
        "PAN_DOCUMENT": "PAN Document",
        "UDYAM_REGISTRATION": "Udyam Registration",
    }
    return known.get(document_type, document_name)


def detect_contradictions(
    fields: Iterable[ExtractedField],
    *,
    document_types: dict[str, str] | None = None,
    document_names: dict[str, str] | None = None,
) -> list[ContradictionFinding]:
    """Find conflicting values for the same field across distinct documents."""

    grouped: dict[str, list[ExtractedField]] = {}
    for field in fields:
        grouped.setdefault(field.field_name, []).append(field)

    document_types = document_types or {}
    document_names = document_names or {}
    findings: list[ContradictionFinding] = []

    for field_name, candidates in grouped.items():
        for left_index, left in enumerate(candidates):
            for right in candidates[left_index + 1 :]:
                if left.document_id == right.document_id:
                    continue
                left_value = left.normalized_value if left.normalized_value is not None else left.value
                right_value = right.normalized_value if right.normalized_value is not None else right.value
                if _same_value(left_value, right_value):
                    continue

                left_type = document_types.get(left.document_id, "")
                right_type = document_types.get(right.document_id, "")
                left_label = _source_label(
                    left_type, document_names.get(left.document_id, left.document_id)
                )
                right_label = _source_label(
                    right_type, document_names.get(right.document_id, right.document_id)
                )

                seed = (
                    f"{field_name}|{left.id}|{right.id}|{left_value!r}|{right_value!r}"
                ).encode("utf-8")
                finding_id = f"FND-{hashlib.sha1(seed).hexdigest()[:8].upper()}"

                findings.append(
                    ContradictionFinding(
                        finding_id=finding_id,
                        field_name=field_name,
                        left_field_id=left.id,
                        right_field_id=right.id,
                        left_value=left_value,
                        right_value=right_value,
                        left_source_label=left_label,
                        right_source_label=right_label,
                        explanation=(
                            f"The extracted {field_name} value in {left_label} "
                            f"({left_value}) differs from the value in {right_label} "
                            f"({right_value}). This discrepancy requires review."
                        ),
                        requires_manual_review=True,
                    )
                )

    return findings


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.strip().casefold() == right.strip().casefold()
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left) == float(right)
    return left == right
