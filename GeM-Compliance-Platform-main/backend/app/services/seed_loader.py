"""Load and validate JSON seed fixtures against the shared domain contract."""

import json
from pathlib import Path
from typing import Any, TypeVar, Type

from pydantic import BaseModel

from app.models.domain import (
    AuditEvent,
    Bidder,
    ComplianceResult,
    Document,
    Evidence,
    ExtractedField,
    RuleDefinition,
    Tender,
    TenderRequirement,
    Verification,
)

MODEL_BY_FILE: dict[str, Type[BaseModel]] = {
    "tenders.json": Tender,
    "requirements.json": TenderRequirement,
    "bidders.json": Bidder,
    "documents.json": Document,
    "extracted_fields.json": ExtractedField,
    "evidence.json": Evidence,
    "verifications.json": Verification,
    "compliance_results.json": ComplianceResult,
    "audit_events.json": AuditEvent,
    "rules.json": RuleDefinition,
}

T = TypeVar("T", bound=BaseModel)


def load_json_fixture(path: Path, model_type: Type[T]) -> list[T]:
    with path.open("r", encoding="utf-8") as file:
        raw: Any = json.load(file)

    if not isinstance(raw, list):
        raise ValueError(f"Fixture must contain a JSON array: {path}")

    return [model_type.model_validate(item) for item in raw]


def load_all_fixtures(fixtures_dir: Path) -> dict[str, list[BaseModel]]:
    loaded: dict[str, list[BaseModel]] = {}
    for filename, model_type in MODEL_BY_FILE.items():
        loaded[filename] = load_json_fixture(fixtures_dir / filename, model_type)
    return loaded
