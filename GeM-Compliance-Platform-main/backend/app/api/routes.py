"""HTTP routes for the prototype's canonical backend workflow."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ai.extraction.explanation_generator import generate_explanation_from_result
from ai.extraction.pdf_reader import extract_pages_from_pdf, pages_from_text
from ai.extraction.requirement_extractor import extract_requirements
from app.api.schemas import (
    AuditListResponse,
    AuditTrailResponse,
    BidderPassportResponse,
    ContradictionExplanationRequest,
    DraftClarificationRequest,
    DraftClarificationResponse,
    DocumentProcessRequest,
    DocumentProcessResponse,
    EvaluateComplianceRequest,
    EvaluationResponse,
    EvidenceChainResponse,
    EvidenceListResponse,
    ExplanationResponse,
    HealthResponse,
    OfficerAuditEvent,
    OfficerDecisionRequest,
    OfficerDecisionResponse,
    ResultBundleResponse,
    TenderExtractionResponse,
    TenderIntakeRequest,
    TenderIntakeResponse,
    VerificationListResponse,
    VerificationProviderInfo,
    VerificationProvidersResponse,
    VerificationRequest,
)
from app.api.state import AppState
from app.models.domain import Bidder, ComplianceResult, Tender, TenderRequirement
from app.rules.registry import rule_id_for
from app.services.requirement_adapter import adapt_requirement_candidates

router = APIRouter(prefix="/api/v1")


def get_state() -> AppState:
    """Dependency placeholder replaced by ``app.main`` during app creation."""

    raise RuntimeError("Application state dependency was not configured")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _format_inr(value: Any) -> str:
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    crore = number / 10_000_000
    if abs(crore - round(crore)) < 1e-9:
        return f"₹{int(round(crore))}.00 Crore"
    return f"₹{crore:.2f} Crore"


def _latest_verifications_for_bidder(state: AppState, bidder_id: str):
    latest_by_evidence: dict[str, Any] = {}
    for evidence in state.workflow.evidence_engine.get_all_evidence():
        if evidence.bidder_id != bidder_id:
            continue
        verifications = state.workflow.evidence_engine.get_verifications_for_evidence(evidence.id)
        if verifications:
            latest_by_evidence[evidence.id] = sorted(
                verifications, key=lambda item: (item.checked_at, item.id), reverse=True
            )[0]
    return list(latest_by_evidence.values())


def _build_officer_event(
    *,
    tender_id: str,
    bidder_id: str,
    disposition: str,
    note: str,
    timestamp: datetime,
    event_id: str,
) -> OfficerAuditEvent:
    payload = {
        "id": event_id,
        "timestamp": timestamp.isoformat(),
        "actor_type": "OFFICER",
        "action": "OFFICER_DISPOSITION_COMMITTED",
        "tender_id": tender_id,
        "bidder_id": bidder_id,
        "disposition": disposition,
        "note": note,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return OfficerAuditEvent(
        id=event_id,
        timestamp=timestamp,
        actor_type="OFFICER",
        action="OFFICER_DISPOSITION_COMMITTED",
        tender_id=tender_id,
        bidder_id=bidder_id,
        disposition=disposition,
        note=note,
        details="Officer disposition recorded by the prototype audit API.",
        sha256_hash=f"SHA256:{digest}",
    )


def _audit_trail(state: AppState, tender_id: str, bidder_id: str) -> list[OfficerAuditEvent]:
    system_events = [
        OfficerAuditEvent(
            **event.model_dump(mode="json")
        )
        for event in state.workflow.get_audit_history(tender_id, bidder_id)
    ]
    officer_events = [
        OfficerAuditEvent.model_validate(event)
        for event in state.officer_events
        if event.get("tender_id") == tender_id and event.get("bidder_id") == bidder_id
    ]
    return sorted(system_events + officer_events, key=lambda item: (item.timestamp, item.id))


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(state: AppState = Depends(get_state)) -> HealthResponse:
    return HealthResponse(verification_mode=state.verification.mode)



def _identify_seed_tender(page_text: str, file_name: str, state: AppState) -> tuple[Tender, list[TenderRequirement], str]:
    """Identify one of the two controlled prototype tenders from the uploaded document content.

    The decision is made from extracted PDF text, never from a frontend tender selector.
    """
    candidates = [
        ("NPIA/EDU-ICT/2026/014", "TND-001"),
        ("NPIA/NETSEC/2026/018", "TND-002"),
    ]
    normalized = page_text.upper()
    for reference, tender_id in candidates:
        if reference in normalized:
            tender = state.workflow.get_tender(tender_id)
            return tender, state.workflow.get_requirements_for_tender(tender_id), "REFERENCE_MATCH"

    raise ValueError(
        "This prototype intake recognizes the supplied Tender_A.pdf or Tender_B.pdf document formats. "
        "No supported tender reference was found in the uploaded PDF."
    )


@router.get("/tenders", response_model=list[Tender], tags=["tenders"])
def list_tenders(state: AppState = Depends(get_state)):
    return [item.model_dump(mode="json") for item in state.workflow.list_tenders()]


@router.get("/tenders/{tender_id}", response_model=Tender, tags=["tenders"])
def get_tender(tender_id: str, state: AppState = Depends(get_state)):
    try:
        tender = state.workflow.get_tender(tender_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return tender.model_dump(mode="json")


@router.get("/tenders/{tender_id}/requirements", response_model=list[TenderRequirement], tags=["tenders"])
def list_requirements(tender_id: str, state: AppState = Depends(get_state)):
    try:
        requirements = state.workflow.get_requirements_for_tender(tender_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [item.model_dump(mode="json") for item in requirements]


@router.post("/tenders/{tender_id}/extract", response_model=TenderExtractionResponse, tags=["tenders"])
def extract_tender_requirements(
    tender_id: str,
    live: bool = False,
    state: AppState = Depends(get_state),
) -> TenderExtractionResponse:
    """Refresh requirements from the canonical fixture, or run the real LLM path when requested."""

    try:
        tender = state.workflow.get_tender(tender_id)
        canonical_requirements = state.workflow.get_requirements_for_tender(tender_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    source_document_id = tender.documents[0] if tender.documents else f"DOC-{tender_id}"
    if live and not os.getenv("LLM_API_KEY"):
        raise HTTPException(status_code=503, detail="LLM_API_KEY is not configured. Refresh mode can still load the frozen canonical fixture.")

    use_live = live

    if not use_live:
        return TenderExtractionResponse(
            tender=tender,
            requirements=canonical_requirements,
            extraction_method="CANONICAL_SEED_FIXTURE",
            ocr_used=False,
            ai_used=False,
            mean_confidence=(
                sum(item.confidence for item in canonical_requirements) / len(canonical_requirements)
                if canonical_requirements
                else None
            ),
            message=(
                "Loaded the frozen prototype tender requirements. Set LLM_API_KEY and call "
                "?live=true to exercise the real LLM extraction path."
            ),
        )

    pdf_map = {
        "TND-001": _repo_root() / "data" / "tenders" / "Tender_A_Sample.pdf",
        "TND-002": _repo_root() / "data" / "tenders" / "Tender_B_Sample.pdf",
    }
    pdf_path = pdf_map.get(tender_id)
    if pdf_path is None or not pdf_path.exists():
        raise HTTPException(status_code=500, detail="Live tender extraction source PDF is unavailable")

    try:
        pages = extract_pages_from_pdf(pdf_path)
        page_text = "\n\n".join(page.text for page in pages)
        extraction = extract_requirements(
            tender_id,
            page_text,
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
            pages=pages,
        )
        adapted = adapt_requirement_candidates(
            extraction,
            tender_id=tender_id,
            source_document_id=source_document_id,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM extraction failed: {exc}") from exc

    # The prototype keeps the canonical tender object stable. This response is a live extraction
    # preview; persistence remains fixture-backed so a single LLM error cannot corrupt the demo state.
    return TenderExtractionResponse(
        tender=tender,
        requirements=adapted,
        extraction_method="PYMUPDF+LLM",
        ocr_used=False,
        ai_used=True,
        mean_confidence=(sum(item.confidence for item in adapted) / len(adapted)) if adapted else None,
        message="PyMuPDF page-aware extraction and validated structured LLM requirement extraction completed.",
    )


@router.get("/bidders", response_model=list[Bidder], tags=["bidders"])
def list_bidders(state: AppState = Depends(get_state)):
    return [item.model_dump(mode="json") for item in state.workflow.list_bidders()]


@router.get("/bidders/{bidder_id}", response_model=Bidder, tags=["bidders"])
def get_bidder(bidder_id: str, state: AppState = Depends(get_state)):
    try:
        bidder = state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return bidder.model_dump(mode="json")


@router.get("/bidders/{bidder_id}/evidence", response_model=EvidenceListResponse, tags=["evidence"])
def get_bidder_evidence(bidder_id: str, state: AppState = Depends(get_state)):
    try:
        state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    evidence = [
        item
        for item in state.workflow.evidence_engine.get_all_evidence()
        if item.bidder_id == bidder_id
    ]
    return EvidenceListResponse(evidence=evidence)


@router.get("/bidders/{bidder_id}/passport", response_model=BidderPassportResponse, tags=["bidders"])
def bidder_passport(bidder_id: str, state: AppState = Depends(get_state)) -> BidderPassportResponse:
    try:
        bidder = state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    evidence = [
        item
        for item in state.workflow.evidence_engine.get_all_evidence()
        if item.bidder_id == bidder_id
    ]
    verifications = _latest_verifications_for_bidder(state, bidder_id)
    turnover_fields = [
        field
        for field in state.workflow._extracted_fields.values()
        if field.field_name == "average_annual_turnover"
        and state.workflow._documents.get(field.document_id, None) is not None
        and state.workflow._documents[field.document_id].bidder_id == bidder_id
    ]
    declared = next((field.normalized_value or field.value for field in turnover_fields if field.document_id == "DOC-002"), None)
    audited = next((field.normalized_value or field.value for field in turnover_fields if field.document_id == "DOC-001"), None)

    return BidderPassportResponse(
        bidder=bidder,
        identity={
            "legal_name": bidder.legal_name,
            "pan": bidder.pan,
            "gstin": bidder.gstin,
            "udyam": bidder.udyam,
            "address": bidder.address,
        },
        evidence=evidence,
        verifications=verifications,
        financial_summary={
            "declared_turnover": declared,
            "declared_turnover_display": _format_inr(declared),
            "verified_turnover": audited,
            "verified_turnover_display": _format_inr(audited),
            "variance": (float(audited) - float(declared)) if declared is not None and audited is not None else None,
            "variance_display": (
                _format_inr(abs(float(declared) - float(audited)))
                if declared is not None and audited is not None
                else "—"
            ),
            "audited_document_id": "DOC-001",
            "self_declaration_document_id": "DOC-002",
        },
        verification_mode=state.verification.mode,
        tender_history=[
            {
                "tender_id": tender_id,
                "tender_reference": state.workflow.get_tender(tender_id).reference_no,
                "tender_title": state.workflow.get_tender(tender_id).title,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "summary": dict(state.workflow.run(tender_id=tender_id, bidder_id=bidder_id).get("summary", {})),
            }
            for tender_id in state.reviewed_tenders_by_bidder.get(bidder_id, [])
        ],
    )


@router.post("/bidders/{bidder_id}/verify", response_model=dict, tags=["verification"])
def verify_bidder(bidder_id: str, state: AppState = Depends(get_state)):
    try:
        bidder = state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    targets = [
        ("gst", bidder.gstin, "gst_status"),
        ("pan", bidder.pan, "pan_status"),
        ("udyam", bidder.udyam, "udyam_status"),
    ]
    # Financial verification is included because it is part of the reusable passport evidence set.
    audited_evidence = next(
        (
            item for item in state.workflow.evidence_engine.get_all_evidence()
            if item.bidder_id == bidder_id
            and item.field_name == "average_annual_turnover"
            and item.document_id == "DOC-001"
        ),
        None,
    )
    if audited_evidence is not None:
        targets.append(("financial", bidder.id, "average_annual_turnover"))

    results: list[dict[str, Any]] = []
    checked_at = datetime.now(timezone.utc)
    for kind, subject, field_name in targets:
        evidence = next(
            (
                item for item in state.workflow.evidence_engine.get_all_evidence()
                if item.bidder_id == bidder_id and item.field_name == field_name
            ),
            None,
        )
        if evidence is None:
            continue
        try:
            verification = state.verification.verify(
                kind=kind,
                subject=subject,
                evidence_id=evidence.id,
                checked_at=checked_at,
            )
            # Mock connectors use deterministic verification IDs. Replace an existing record with the same
            # ID only by retaining the first stored object, preserving idempotence.
            existing = next(
                (
                    item for item in state.workflow.evidence_engine.get_verifications_for_evidence(evidence.id)
                    if item.id == verification.id
                ),
                None,
            )
            if existing is None:
                state.workflow.evidence_engine.attach_verification(verification)
            else:
                verification = existing
            results.append(verification.model_dump(mode="json"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Verification provider error: {exc}") from exc

    return {
        "verified": all(item.get("status") == "VERIFIED" for item in results),
        "timestamp": checked_at.isoformat(),
        "mode": state.verification.mode,
        "source": "MOCK_VERIFICATION_ONLY",
        "verifications": results,
    }


@router.post("/compliance/evaluate", response_model=EvaluationResponse, tags=["compliance"])
def evaluate_compliance(
    request: EvaluateComplianceRequest,
    state: AppState = Depends(get_state),
) -> EvaluationResponse:
    try:
        report = state.workflow.run(
            tender_id=request.tender_id,
            bidder_id=request.bidder_id,
            evaluated_at=request.evaluated_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    reviewed = state.reviewed_tenders_by_bidder.setdefault(request.bidder_id, [])
    if request.tender_id not in reviewed:
        reviewed.append(request.tender_id)
    return EvaluationResponse.model_validate(report)


@router.get("/compliance/results/{result_id}", response_model=ResultBundleResponse, tags=["compliance"])
def get_result(result_id: str, state: AppState = Depends(get_state)) -> ResultBundleResponse:
    try:
        bundle = state.workflow.get_result_bundle(result_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResultBundleResponse.model_validate(bundle)


@router.get("/compliance/{tender_id}/{bidder_id}/results", response_model=list, tags=["compliance"])
def list_results(tender_id: str, bidder_id: str, state: AppState = Depends(get_state)):
    try:
        state.workflow.get_tender(tender_id)
        state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [item.model_dump(mode="json") for item in state.workflow.get_results(tender_id, bidder_id)]


@router.get("/compliance/{tender_id}/{bidder_id}/audit", response_model=AuditTrailResponse, tags=["audit"])
def audit_history(tender_id: str, bidder_id: str, state: AppState = Depends(get_state)) -> AuditTrailResponse:
    try:
        state.workflow.get_tender(tender_id)
        state.workflow.get_bidder(bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuditTrailResponse(audit_events=_audit_trail(state, tender_id, bidder_id))


@router.get("/audit/{tender_id}/{bidder_id}", response_model=AuditTrailResponse, tags=["audit"])
def audit_history_alias(tender_id: str, bidder_id: str, state: AppState = Depends(get_state)) -> AuditTrailResponse:
    return audit_history(tender_id, bidder_id, state)


@router.post("/audit/commit", response_model=OfficerDecisionResponse, tags=["audit"])
def commit_officer_decision(
    request: OfficerDecisionRequest,
    state: AppState = Depends(get_state),
) -> OfficerDecisionResponse:
    try:
        state.workflow.get_tender(request.tender_id)
        state.workflow.get_bidder(request.bidder_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    timestamp = datetime.now(timezone.utc)
    event_id = f"AUD-OFFICER-{len(state.officer_events) + 1:03d}"
    event = _build_officer_event(
        tender_id=request.tender_id,
        bidder_id=request.bidder_id,
        disposition=request.disposition,
        note=request.note,
        timestamp=timestamp,
        event_id=event_id,
    )
    state.officer_events.append(event.model_dump(mode="json"))
    return OfficerDecisionResponse(
        message="Officer disposition appended to the prototype audit trail.",
        audit_event=event,
    )


@router.get("/evidence/{evidence_id}", response_model=dict, tags=["evidence"])
def get_evidence(evidence_id: str, state: AppState = Depends(get_state)):
    try:
        evidence = state.workflow.evidence_engine.get_evidence(evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return evidence.model_dump(mode="json")


@router.get("/evidence/{evidence_id}/verifications", response_model=VerificationListResponse, tags=["evidence"])
def get_evidence_verifications(evidence_id: str, state: AppState = Depends(get_state)) -> VerificationListResponse:
    try:
        verifications = state.workflow.evidence_engine.get_verifications_for_evidence(evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VerificationListResponse(verifications=verifications)


@router.get("/evidence/{evidence_id}/chain", response_model=EvidenceChainResponse, tags=["evidence"])
def get_evidence_chain(evidence_id: str, state: AppState = Depends(get_state)) -> EvidenceChainResponse:
    try:
        chain = state.workflow.get_evidence_chain_for_evidence(evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvidenceChainResponse(evidence_chain=chain)


@router.get("/verification/providers", response_model=VerificationProvidersResponse, tags=["verification"])
def verification_providers(state: AppState = Depends(get_state)) -> VerificationProvidersResponse:
    source_by_kind = {
        "gst": "Mock GST Verification",
        "pan": "Mock PAN Verification",
        "udyam": "Mock Udyam Verification",
        "financial": "Mock Financial Verification",
    }
    providers = [
        VerificationProviderInfo(
            kind=kind,
            mode=state.verification.mode_for(kind),
            source_name=source_by_kind.get(kind, kind),
            configured=True,
        )
        for kind in state.verification.supported_kinds()
    ]
    return VerificationProvidersResponse(providers=providers)


@router.post("/verification/verify", response_model=dict, tags=["verification"])
def verify(request: VerificationRequest, state: AppState = Depends(get_state)):
    try:
        state.workflow.evidence_engine.get_evidence(request.evidence_id)
        verification = state.verification.verify(
            kind=request.kind,
            subject=request.subject,
            evidence_id=request.evidence_id,
            checked_at=request.checked_at,
        )
        existing = next(
            (
                item
                for item in state.workflow.evidence_engine.get_verifications_for_evidence(request.evidence_id)
                if item.id == verification.id
            ),
            None,
        )
        if existing is None:
            state.workflow.evidence_engine.attach_verification(verification)
        else:
            verification = existing
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Verification provider error") from exc
    return verification.model_dump(mode="json")


@router.post("/ai/explain-contradiction", response_model=ExplanationResponse, tags=["ai"])
def explain_contradiction(
    request: ContradictionExplanationRequest,
    state: AppState = Depends(get_state),
) -> ExplanationResponse:
    try:
        bundle = state.workflow.get_result_bundle(request.result_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result: ComplianceResult = bundle["result"]
    requirement = state.workflow._requirements[result.requirement_id]
    verification = bundle["verifications"][-1] if bundle["verifications"] else None
    declared_value = None
    all_requirement_evidence = state.workflow.evidence_engine.get_evidence_for_requirement(
        bidder_id=result.bidder_id,
        requirement_id=result.requirement_id,
    )
    for evidence in all_requirement_evidence:
        if evidence.source_label.lower().startswith("self declaration"):
            declared_value = evidence.value
            break

    if os.getenv("LLM_API_KEY"):
        try:
            explanation = generate_explanation_from_result(
                result,
                requirement,
                verification,
                declared_value=declared_value,
                model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
            )
            return ExplanationResponse(
                source="LLM_EXPLANATION",
                model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
                explanation=explanation,
            )
        except Exception:
            pass

    status = result.status.value
    if declared_value is not None and result.actual is not None and declared_value != result.actual:
        explanation = (
            f"The bidder-declared turnover is {_format_inr(declared_value)}, while the audited/verified "
            f"turnover used by the deterministic rule is {_format_inr(result.actual)}. The resulting "
            f"discrepancy is recorded for officer review; the system does not label it as fraud. "
            f"The compliance result remains {status}."
        )
    else:
        explanation = result.explanation

    return ExplanationResponse(
        source="DETERMINISTIC_FACTUAL_FALLBACK",
        model="not_used",
        explanation=explanation,
    )


@router.post("/ai/draft-clarification", response_model=DraftClarificationResponse, tags=["ai"])
def draft_clarification(request: DraftClarificationRequest) -> DraftClarificationResponse:
    draft = (
        f"Subject: Clarification request for Tender {request.tender_ref}\n\n"
        f"To: {request.bidder_name}\n\n"
        "During document review, the submitted turnover information shows a discrepancy between the "
        f"declared and audited values (variance noted: {request.variance}). Please provide a clarification "
        "and supporting documents explaining the difference. This request is for officer review and does "
        "not by itself determine final eligibility.\n"
    )
    return DraftClarificationResponse(source="DETERMINISTIC_TEMPLATE", draft=draft)


@router.post("/reviews/intake", response_model=TenderIntakeResponse, tags=["reviews"])
def intake_tender_document(request: TenderIntakeRequest, state: AppState = Depends(get_state)) -> TenderIntakeResponse:
    """Open a tender review from an uploaded PDF and immediately evaluate the seeded bidder evidence.

    This is deliberately a controlled prototype intake: the PDF is genuinely read by the backend,
    then matched to one of the two supplied synthetic tender fixtures. The frontend never chooses
    the tender ID directly.
    """
    raw_data = request.file_data
    if "," in raw_data and raw_data.startswith("data:"):
        raw_data = raw_data.split(",", 1)[1]
    try:
        content = base64.b64decode(raw_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="file_data is not valid base64") from exc

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 50MB prototype upload limit")

    if request.mime_type != "application/pdf" and not request.file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Tender intake requires a PDF document")

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            temp_path = tmp.name
        pages = extract_pages_from_pdf(temp_path)
        page_text = "\n\n".join(page.text for page in pages)
        tender, requirements, recognition = _identify_seed_tender(page_text, request.file_name, state)
    except NotImplementedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Tender PDF could not be read: {exc}") from exc
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    ai_used = bool(os.getenv("LLM_API_KEY"))
    extraction_method = "PYMUPDF+CANONICAL_ADAPTER"
    message = (
        f"Uploaded document recognized by extracted reference ({recognition}). "
        "The controlled prototype then evaluated the bidder using the backend rule engine."
    )

    try:
        report = state.workflow.run(tender_id=tender.id, bidder_id="BIDDER-001")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    reviewed = state.reviewed_tenders_by_bidder.setdefault("BIDDER-001", [])
    if tender.id not in reviewed:
        reviewed.append(tender.id)

    return TenderIntakeResponse(
        file_name=request.file_name,
        tender=tender,
        requirements=requirements,
        evaluation=EvaluationResponse.model_validate(report),
        extraction_method=extraction_method,
        ocr_used=False,
        ai_used=ai_used,
        mean_confidence=(sum(item.confidence for item in requirements) / len(requirements)) if requirements else None,
        message=message,
    )


@router.post("/documents/ocr-process", response_model=DocumentProcessResponse, tags=["documents"])
def process_document(request: DocumentProcessRequest) -> DocumentProcessResponse:
    """Process an uploaded tender document for extraction preview.

    This endpoint is intentionally a preview path: it does not mutate the canonical seeded demo state.
    For PDFs, page-aware PyMuPDF extraction runs first. OCR remains a separately isolated future path.
    """

    raw_data = request.file_data
    if "," in raw_data and raw_data.startswith("data:"):
        raw_data = raw_data.split(",", 1)[1]
    try:
        content = base64.b64decode(raw_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="file_data is not valid base64") from exc

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 50MB prototype upload limit")

    suffix = Path(request.file_name).suffix.lower()
    pages = []
    temp_path: str | None = None
    try:
        if suffix == ".pdf" or request.mime_type == "application/pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                temp_path = tmp.name
            pages = extract_pages_from_pdf(temp_path)
            extraction_method = "PYMUPDF"
        elif suffix == ".txt" or request.mime_type.startswith("text/"):
            pages = pages_from_text(content.decode("utf-8", errors="replace"))
            extraction_method = "TEXT"
        else:
            raise HTTPException(
                status_code=415,
                detail="Prototype document ingestion supports PDF and plain text. OCR/image fallback is isolated but not enabled on this path.",
            )
    except NotImplementedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Document text extraction failed: {exc}") from exc
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="LLM_API_KEY is not configured. The seeded prototype workflow does not require live upload extraction; configure the key to use this upload preview.",
        )

    page_text = "\n\n".join(page.text for page in pages)
    preview_tender_id = "TND-UPLOAD-PREVIEW"
    preview_document_id = "DOC-UPLOAD-" + hashlib.sha1(request.file_name.encode("utf-8")).hexdigest()[:8].upper()
    try:
        extraction = extract_requirements(
            preview_tender_id,
            page_text,
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
            pages=pages,
        )
        requirements = adapt_requirement_candidates(
            extraction,
            tender_id=preview_tender_id,
            source_document_id=preview_document_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live AI extraction failed: {exc}") from exc

    return DocumentProcessResponse(
        file_name=request.file_name,
        extraction_method=f"{extraction_method}+LLM",
        ocr_used=False,
        ai_used=True,
        mean_confidence=(sum(item.confidence for item in requirements) / len(requirements)) if requirements else None,
        extracted_requirements=requirements,
        message="Document processed successfully. Requirements are returned as a preview and are not written into the frozen demo dataset.",
    )
