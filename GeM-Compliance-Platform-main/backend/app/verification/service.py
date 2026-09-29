"""Application-facing verification boundary.

The API layer should depend on this service rather than importing individual
mock connectors. The service keeps provider selection behind one small
interface, which lets the prototype use deterministic mock sources today and
lets authorized API Setu/provider adapters be plugged in later.
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from app.models.domain import Verification
from app.verification import (
    MockFinancialVerificationConnector,
    MockGSTConnector,
    MockPANConnector,
    MockUdyamConnector,
    MockOEMConnector,
    MockDebarmentConnector,
)
from app.verification.base import VerificationConnector


SUPPORTED_KINDS = ("gst", "pan", "udyam", "financial", "oem", "debarment")


class VerificationService:
    """Dispatch verification requests to the configured connector set."""

    def __init__(
        self,
        connectors: Mapping[str, VerificationConnector] | None = None,
        *,
        mode: str = "mock",
    ) -> None:
        self.mode = mode.strip().lower()
        if self.mode not in {"mock", "api_setu"}:
            raise ValueError("verification mode must be 'mock' or 'api_setu'")

        self._connectors: dict[str, VerificationConnector] = dict(
            connectors
            or {
                "gst": MockGSTConnector(),
                "pan": MockPANConnector(),
                "udyam": MockUdyamConnector(),
                "financial": MockFinancialVerificationConnector(),
                "oem": MockOEMConnector(),
                "debarment": MockDebarmentConnector(),
            }
        )

    def supported_kinds(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))

    def get_connector(self, kind: str) -> VerificationConnector:
        normalized = kind.strip().lower()
        try:
            return self._connectors[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported verification kind {kind!r}. "
                f"Supported kinds: {', '.join(SUPPORTED_KINDS)}"
            ) from exc

    def verify(
        self,
        *,
        kind: str,
        subject: str,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        """Run one verification through the selected provider connector."""

        connector = self.get_connector(kind)
        return connector.verify(
            subject,
            evidence_id=evidence_id,
            checked_at=checked_at,
        )

    def mode_for(self, _kind: str) -> str:
        """Expose the provider mode without leaking credentials."""

        return self.mode
