"""Mock debarment-registry connector for the prototype."""
from __future__ import annotations
from datetime import datetime
from app.models.domain import Verification
from app.verification.base import MockVerificationStore, VerificationConnector, build_verification

class MockDebarmentConnector:
    """Return deterministic debarment clearance from the mock registry."""
    source_name = "Mock Debarment Registry"
    category = "debarment"
    def __init__(self, store: MockVerificationStore | None = None) -> None:
        self._store = store or MockVerificationStore.from_default_file()
    def verify(self, subject: str, *, evidence_id: str, checked_at: datetime | None = None) -> Verification:
        normalized = subject.strip().upper()
        if not normalized:
            raise ValueError("Debarment verification subject must be non-empty")
        return build_verification(evidence_id=evidence_id, source_name=self.source_name, subject=normalized, record=self._store.lookup(self.category, normalized), checked_at=checked_at)
_: type[VerificationConnector] = MockDebarmentConnector
