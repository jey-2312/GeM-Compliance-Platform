"""Shared domain contract for the prototype.

This module intentionally contains only the entities defined by the shared
prototype development specification. It is the backend-side representation
of the JSON/domain contract shared with the AI and frontend workstreams.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PENDING = "PENDING"
    UNVERIFIABLE = "UNVERIFIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DomainModel(BaseModel):
    """Base configuration for stable shared contract models."""

    model_config = ConfigDict(extra="forbid")


class Tender(DomainModel):
    id: str
    title: str
    reference_no: str
    closing_date: date
    documents: list[str]
    requirements: list[str]
    status: str


class TenderRequirement(DomainModel):
    id: str
    tender_id: str
    type: str
    title: str
    description: str
    operator: str
    threshold: float | int | None = None
    unit: str | None = None
    mandatory: bool
    source_document_id: str
    source_page: int
    confidence: float = Field(ge=0.0, le=1.0)
    rule_id: str


class Bidder(DomainModel):
    id: str
    legal_name: str
    pan: str
    gstin: str
    udyam: str
    address: str
    evidence_ids: list[str]


class Document(DomainModel):
    id: str
    bidder_id: str
    name: str
    document_type: str
    path_or_uri: str
    page_count: int = Field(ge=1)
    text_extraction_method: str
    ocr_used: bool
    uploaded_at: datetime


class ExtractedField(DomainModel):
    id: str
    document_id: str
    field_name: str
    value: Any
    unit: str | None = None
    normalized_value: Any | None = None
    raw_text: str
    page: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: str


class Evidence(DomainModel):
    id: str
    bidder_id: str
    requirement_id: str
    document_id: str
    page: int = Field(ge=1)
    evidence_type: str
    field_name: str
    value: Any
    unit: str | None = None
    source_label: str
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: str
    notes: str | None = None


class Verification(DomainModel):
    id: str
    evidence_id: str
    source_type: str
    source_name: str
    checked_at: datetime
    status: str
    verified_value: Any | None = None
    details: str


class ComplianceResult(DomainModel):
    id: str
    tender_id: str
    bidder_id: str
    requirement_id: str
    status: ComplianceStatus
    rule_id: str
    expected: Any
    actual: Any
    evidence_ids: list[str]
    finding_ids: list[str]
    explanation: str
    evaluated_at: datetime
    gap_to_compliance: str | None = None
    critical: bool = False


class AuditEvent(DomainModel):
    id: str
    timestamp: datetime
    actor_type: str
    action: str
    tender_id: str
    bidder_id: str
    requirement_id: str
    rule_id: str
    result_id: str
    details: str


class RuleDefinition(DomainModel):
    id: str
    type: str
    field: str
    operator: str
    threshold_source: str
    mandatory: bool
    version: str
