"""Verification connector boundary and prototype mock implementations."""

from app.verification.mock_financial import MockFinancialVerificationConnector
from app.verification.mock_gst import MockGSTConnector
from app.verification.mock_pan import MockPANConnector
from app.verification.mock_udyam import MockUdyamConnector
from app.verification.mock_oem import MockOEMConnector
from app.verification.mock_debarment import MockDebarmentConnector

__all__ = [
    "MockFinancialVerificationConnector",
    "MockGSTConnector",
    "MockPANConnector",
    "MockUdyamConnector",
    "MockOEMConnector",
    "MockDebarmentConnector",
]
