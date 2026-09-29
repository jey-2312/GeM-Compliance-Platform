"""Mock PAN verification connector for the prototype."""

from __future__ import annotations

from datetime import datetime

from app.models.domain import Verification
from app.verification.base import MockVerificationStore, build_verification


class MockPANConnector:
    """Return deterministic PAN verification records from mock data."""

    source_name = "Mock PAN Verification"
    category = "pan"

    def __init__(self, store: MockVerificationStore | None = None) -> None:
        self._store = store or MockVerificationStore.from_default_file()

    def verify(
        self,
        pan: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        normalized = _normalize_identifier(pan)
        record = self._store.lookup(self.category, normalized)
        return build_verification(
            evidence_id=evidence_id,
            source_name=self.source_name,
            subject=normalized,
            record=record,
            checked_at=checked_at,
        )


def _normalize_identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("PAN must be a non-empty string")
    return value.strip().upper()
