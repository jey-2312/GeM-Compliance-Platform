from datetime import datetime, timezone

import pytest

from app.models.domain import Verification
from app.verification.base import (
    MockVerificationStore,
    VERIFICATION_NOT_FOUND,
    VERIFICATION_VERIFIED,
)
from app.verification.mock_financial import MockFinancialVerificationConnector
from app.verification.mock_gst import MockGSTConnector
from app.verification.mock_pan import MockPANConnector
from app.verification.mock_udyam import MockUdyamConnector


CHECKED_AT = datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc)


def test_mock_gst_returns_active_for_seed_bidder() -> None:
    result = MockGSTConnector().verify(
        "29ABCDE1234F1Z5", evidence_id="EVD-001", checked_at=CHECKED_AT
    )

    assert isinstance(result, Verification)
    assert result.evidence_id == "EVD-001"
    assert result.source_type == "MOCK_GOVERNMENT_SOURCE"
    assert result.source_name == "Mock GST Verification"
    assert result.status == VERIFICATION_VERIFIED
    assert result.verified_value == "ACTIVE"
    assert result.checked_at == CHECKED_AT


def test_mock_pan_returns_valid_for_seed_bidder() -> None:
    result = MockPANConnector().verify(
        "ABCDE1234F", evidence_id="EVD-002", checked_at=CHECKED_AT
    )

    assert result.status == VERIFICATION_VERIFIED
    assert result.verified_value == "VALID"


def test_mock_udyam_returns_active_for_seed_bidder() -> None:
    result = MockUdyamConnector().verify(
        "UDYAM-KL-00-0000000", evidence_id="EVD-003", checked_at=CHECKED_AT
    )

    assert result.status == VERIFICATION_VERIFIED
    assert result.verified_value == "ACTIVE"


def test_mock_financial_returns_verified_4_8_crore() -> None:
    result = MockFinancialVerificationConnector().verify(
        "BIDDER-001", evidence_id="EVD-012", checked_at=CHECKED_AT
    )

    assert result.status == VERIFICATION_VERIFIED
    assert result.verified_value == 48_000_000


def test_unknown_gstin_does_not_become_verified() -> None:
    result = MockGSTConnector().verify(
        "99UNKNOWN0000XXX", evidence_id="EVD-X", checked_at=CHECKED_AT
    )

    assert result.status == VERIFICATION_NOT_FOUND
    assert result.verified_value is None


def test_identifiers_are_normalized_before_lookup() -> None:
    result = MockPANConnector().verify(
        " abcde1234f ", evidence_id="EVD-002", checked_at=CHECKED_AT
    )

    assert result.status == VERIFICATION_VERIFIED
    assert result.verified_value == "VALID"


def test_mock_store_rejects_malformed_record() -> None:
    store = MockVerificationStore(
        {"gst": {"X": {"verified_value": "ACTIVE", "details": "missing status"}}}
    )

    with pytest.raises(ValueError, match="status"):
        from app.verification.base import build_verification

        build_verification(
            evidence_id="EVD-X",
            source_name="Mock GST Verification",
            subject="X",
            record=store.lookup("gst", "X"),
            checked_at=CHECKED_AT,
        )
