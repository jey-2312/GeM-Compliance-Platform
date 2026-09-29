"""Provider-neutral API Setu HTTP connector boundary.

This module intentionally does not hard-code GST/PAN/Udyam endpoint URLs or
provider-specific request/response schemas. API Setu's current SOP directs
consumers to use the endpoint URLs and request/response formats supplied by
the individual API documentation, and notes that authentication can vary by
publisher. A concrete adapter should therefore subclass this boundary once
the team has an approved API subscription and the provider's exact contract.

The connector is deliberately injectable and is not enabled by default in the
prototype. Mock connectors remain the working implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Mapping

import httpx

from app.models.domain import Verification


class APISetuConnectorError(RuntimeError):
    """Raised when an API Setu request cannot produce a Verification."""


class APISetuConnector(ABC):
    """Base class for one authorized API Setu/provider integration."""

    source_type = "API_SETU_PROVIDER"

    def __init__(
        self,
        *,
        source_name: str,
        endpoint_url: str,
        client_id: str,
        api_key: str,
        timeout_seconds: float = 15.0,
        client_id_header: str = "X-APISETU-CLIENTID",
        api_key_header: str = "X-APISETU-APIKEY",
    ) -> None:
        if not endpoint_url.strip():
            raise ValueError("endpoint_url must be non-empty")
        if not client_id.strip() or not api_key.strip():
            raise ValueError("API Setu credentials must be supplied")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.source_name = source_name
        self.endpoint_url = endpoint_url
        self._client_id = client_id
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client_id_header = client_id_header
        self._api_key_header = api_key_header

    def verify(
        self,
        subject: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        subject = subject.strip()
        if not subject:
            raise ValueError("Verification subject must be non-empty")

        try:
            response = self._request(subject)
            payload = response.json()
        except httpx.HTTPError as exc:
            raise APISetuConnectorError(
                f"API Setu request failed for {self.source_name}: {exc}"
            ) from exc
        except ValueError as exc:
            raise APISetuConnectorError(
                f"API Setu response was not valid JSON for {self.source_name}."
            ) from exc

        if not isinstance(payload, Mapping):
            raise APISetuConnectorError(
                f"API Setu response must be a JSON object for {self.source_name}."
            )

        timestamp = checked_at or datetime.now(timezone.utc)
        return self.parse_response(
            payload,
            evidence_id=evidence_id,
            checked_at=timestamp,
            subject=subject,
        )

    def _request(self, subject: str) -> httpx.Response:
        headers = {
            self._client_id_header: self._client_id,
            self._api_key_header: self._api_key,
            "Accept": "application/json",
        }
        request_kwargs = self.build_request(subject)
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.request(
                request_kwargs["method"],
                self.endpoint_url,
                headers=headers,
                params=request_kwargs.get("params"),
                json=request_kwargs.get("json"),
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise APISetuConnectorError(
                f"API Setu returned HTTP {response.status_code} for {self.source_name}."
            ) from exc
        return response

    @abstractmethod
    def build_request(self, subject: str) -> dict[str, Any]:
        """Return method plus provider-specific params/json for one subject."""

    @abstractmethod
    def parse_response(
        self,
        payload: Mapping[str, Any],
        *,
        evidence_id: str,
        checked_at: datetime,
        subject: str,
    ) -> Verification:
        """Map a provider response into the shared Verification object."""
