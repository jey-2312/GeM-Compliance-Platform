"""HTTP request/response schemas for the prototype API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ai.schemas.models import ContradictionFinding
from app.models.domain import (
    AuditEvent,
    Bidder,
    ComplianceResult,
    Document,
    Evidence,
    ExtractedField,
    RuleDefinition,
    Tender,
    TenderRequirement,
    Verification,
)


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    service: str = "GeM Compliance Platform Backend"
    version: str = "0.1.0"
    verification_mode: str


class EvaluateComplianceRequest(APIModel):
    tender_id: str = Field(min_length=1)
    bidder_id: str = Field(min_length=1)
    evaluated_at: datetime | None = None


class VerificationRequest(APIModel):
    kind: Literal["gst", "pan", "udyam", "financial"]
    subject: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    checked_at: datetime | None = None


class VerificationProviderInfo(APIModel):
    kind: str
    mode: str
    source_name: str
    configured: bool


class VerificationProvidersResponse(APIModel):
    providers: list[VerificationProviderInfo]


class EvaluationResponse(APIModel):
    tender: Tender
    bidder: Bidder
    requirements: list[TenderRequirement]
    passport_verifications: list[Verification]
    findings: list[ContradictionFinding]
    evidence: list[Evidence]
    verifications: list[Verification]
    compliance_results: list[ComplianceResult]
    audit_events: list[AuditEvent]
    evidence_chains: dict[str, dict[str, Any]]
    summary: dict[str, int]


class EvidenceListResponse(APIModel):
    evidence: list[Evidence]


class VerificationListResponse(APIModel):
    verifications: list[Verification]


class AuditListResponse(APIModel):
    audit_events: list[AuditEvent]


class ResultBundleResponse(APIModel):
    result: ComplianceResult
    evidence: list[Evidence]
    verifications: list[Verification]
    audit_events: list[AuditEvent]
    evidence_chain: dict[str, Any]


class EvidenceChainResponse(APIModel):
    evidence_chain: dict[str, Any]


class TenderExtractionResponse(APIModel):
    success: bool = True
    tender: Tender
    requirements: list[TenderRequirement]
    extraction_method: str
    ocr_used: bool
    ai_used: bool
    mean_confidence: float | None = None
    message: str


class BidderPassportResponse(APIModel):
    bidder: Bidder
    identity: dict[str, Any]
    evidence: list[Evidence]
    verifications: list[Verification]
    financial_summary: dict[str, Any]
    verification_mode: str
    tender_history: list[dict[str, Any]] = Field(default_factory=list)


class OfficerDecisionRequest(APIModel):
    tender_id: str = Field(min_length=1)
    bidder_id: str = Field(min_length=1)
    disposition: str = Field(min_length=1)
    note: str = Field(min_length=1)


class OfficerAuditEvent(APIModel):
    id: str
    timestamp: datetime
    actor_type: str
    action: str
    tender_id: str
    bidder_id: str
    requirement_id: str | None = None
    rule_id: str | None = None
    result_id: str | None = None
    details: str | None = None
    disposition: str | None = None
    note: str | None = None
    sha256_hash: str | None = None


class AuditTrailResponse(APIModel):
    audit_events: list[OfficerAuditEvent]


class OfficerDecisionResponse(APIModel):
    success: bool = True
    message: str
    audit_event: OfficerAuditEvent


class ContradictionExplanationRequest(APIModel):
    result_id: str = Field(min_length=1)


class ExplanationResponse(APIModel):
    source: str
    model: str
    explanation: str


class DraftClarificationRequest(APIModel):
    tender_ref: str = Field(min_length=1)
    bidder_name: str = Field(min_length=1)
    variance: str = Field(min_length=1)


class DraftClarificationResponse(APIModel):
    source: str
    draft: str


class DocumentProcessRequest(APIModel):
    file_name: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    file_data: str = Field(min_length=1)
    document_type: str = "TENDER"


class TenderIntakeRequest(APIModel):
    file_name: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    file_data: str = Field(min_length=1)


class TenderIntakeResponse(APIModel):
    success: bool = True
    file_name: str
    tender: Tender
    requirements: list[TenderRequirement]
    evaluation: EvaluationResponse
    extraction_method: str
    ocr_used: bool
    ai_used: bool
    mean_confidence: float | None = None
    message: str


class DocumentProcessResponse(APIModel):
    success: bool = True
    file_name: str
    extraction_method: str
    ocr_used: bool
    ai_used: bool
    mean_confidence: float | None = None
    extracted_requirements: list[TenderRequirement]
    message: str
