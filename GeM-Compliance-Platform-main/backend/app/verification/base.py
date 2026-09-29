"""Common interfaces and helpers for verification connectors.

The prototype deliberately separates the *connector boundary* from the
verification source implementation. Today the implementations below are
mock sources; later, an authorized API Setu/provider integration can implement
this same contract without changing the rule engine.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from app.models.domain import Verification


SOURCE_TYPE_MOCK = "MOCK_GOVERNMENT_SOURCE"

# Verification.status is intentionally a string in the shared domain contract.
# These constants define the small vocabulary used by the prototype connectors.
VERIFICATION_VERIFIED = "VERIFIED"
VERIFICATION_NOT_FOUND = "NOT_FOUND"
VERIFICATION_INVALID = "INVALID"
VERIFICATION_ERROR = "ERROR"


class VerificationConnector(Protocol):
    """Provider-neutral contract used by the compliance backend."""

    source_name: str

    def verify(
        self,
        subject: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        """Verify one subject and return the shared Verification object."""
        ...


class MockVerificationStore:
    """Read-only store for prototype verification responses.

    Keeping mock responses in data/mock_sources instead of burying them inside
    the connector logic makes the mock easy to edit for tests and keeps the
    eventual real connector boundary clean.
    """

    def __init__(self, records: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> None:
        self._records = records

    @classmethod
    def from_default_file(cls) -> "MockVerificationStore":
        path = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "mock_sources"
            / "government_verification.json"
        )
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise ValueError("Mock verification data must be a JSON object")

        return cls(payload)

    def lookup(self, category: str, subject: str) -> Mapping[str, Any] | None:
        category_records = self._records.get(category, {})
        if not isinstance(category_records, Mapping):
            raise ValueError(f"Mock verification category {category!r} is invalid")

        record = category_records.get(subject)
        if record is None:
            return None
        if not isinstance(record, Mapping):
            raise ValueError(
                f"Mock verification record for {category!r}/{subject!r} is invalid"
            )
        return record


def build_verification(
    *,
    evidence_id: str,
    source_name: str,
    subject: str,
    record: Mapping[str, Any] | None,
    checked_at: datetime | None = None,
) -> Verification:
    """Convert a provider/mock response into the shared Verification shape."""

    timestamp = checked_at or datetime.now(timezone.utc)

    if record is None:
        return Verification(
            id=_verification_id(evidence_id, source_name),
            evidence_id=evidence_id,
            source_type=SOURCE_TYPE_MOCK,
            source_name=source_name,
            checked_at=timestamp,
            status=VERIFICATION_NOT_FOUND,
            verified_value=None,
            details=f"Mock source has no record for subject {subject!r}.",
        )

    status = record.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("Mock verification record must contain a non-empty status")

    details = record.get("details")
    if not isinstance(details, str) or not details:
        raise ValueError("Mock verification record must contain non-empty details")

    return Verification(
        id=_verification_id(evidence_id, source_name),
        evidence_id=evidence_id,
        source_type=SOURCE_TYPE_MOCK,
        source_name=source_name,
        checked_at=timestamp,
        status=status,
        verified_value=record.get("verified_value"),
        details=details,
    )


def _verification_id(evidence_id: str, source_name: str) -> str:
    """Create a stable prototype ID for one evidence/source pair."""

    safe_source = "".join(ch if ch.isalnum() else "-" for ch in source_name.upper())
    return f"VER-{evidence_id}-{safe_source}"[:128]
