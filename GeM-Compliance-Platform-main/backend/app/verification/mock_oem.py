"""Mock OEM authorization verification connector for the prototype."""

from __future__ import annotations

from datetime import datetime

from app.models.domain import Verification
from app.verification.base import (
    MockVerificationStore,
    VerificationConnector,
    build_verification,
)


class MockOEMConnector:
    """Return deterministic OEM authorization records from mock data."""

    source_name = "Mock OEM Authorization Verification"
    category = "oem"

    def __init__(self, store: MockVerificationStore | None = None) -> None:
        self._store = store or MockVerificationStore.from_default_file()

    def verify(
        self,
        subject: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        normalized = _normalize_subject(subject)
        record = self._store.lookup(self.category, normalized)
        return build_verification(
            evidence_id=evidence_id,
            source_name=self.source_name,
            subject=normalized,
            record=record,
            checked_at=checked_at,
        )


_: type[VerificationConnector] = MockOEMConnector


def _normalize_subject(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("OEM verification subject must be a non-empty string")
    return value.strip().upper()
