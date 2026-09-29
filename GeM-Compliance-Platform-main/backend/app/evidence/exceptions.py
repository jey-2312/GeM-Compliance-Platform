"""Errors raised by the prototype Evidence Engine."""


class EvidenceEngineError(ValueError):
    """Base error for evidence engine validation and lookup failures."""


class EvidenceValidationError(EvidenceEngineError):
    """Raised when an evidence object cannot be safely created or updated."""


class EvidenceNotFoundError(EvidenceEngineError):
    """Raised when a requested evidence or verification target does not exist."""


class DuplicateEvidenceError(EvidenceEngineError):
    """Raised when a caller tries to register the same evidence ID twice."""


class DuplicateVerificationError(EvidenceEngineError):
    """Raised when a caller tries to register the same verification ID twice."""
