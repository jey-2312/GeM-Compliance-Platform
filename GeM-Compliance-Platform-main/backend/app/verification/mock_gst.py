"""Mock GST verification connector for the prototype."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from app.models.domain import Verification
from app.verification.base import (
    MockVerificationStore,
    VerificationConnector,
    build_verification,
)


class MockGSTConnector:
    """Return deterministic GST verification records from mock data."""

    source_name = "Mock GST Verification"
    category = "gst"

    def __init__(self, store: MockVerificationStore | None = None) -> None:
        self._store = store or MockVerificationStore.from_default_file()

    def verify(
        self,
        gstin: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        normalized = _normalize_identifier(gstin)
        record = self._store.lookup(self.category, normalized)
        return build_verification(
            evidence_id=evidence_id,
            source_name=self.source_name,
            subject=normalized,
            record=record,
            checked_at=checked_at,
        )


# Structural check used during development without coupling runtime behavior
# to typing-only imports.
_: type[VerificationConnector] = MockGSTConnector


def _normalize_identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("GSTIN must be a non-empty string")
    return value.strip().upper()
