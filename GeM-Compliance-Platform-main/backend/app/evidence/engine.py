"""Evidence Engine for the SIH 26100 compliance prototype.

The Evidence Engine is deliberately narrow:

    ExtractedField + Document + Requirement + Bidder
        -> Evidence
        -> Verification association
        -> Evidence lookup / chain assembly

It does NOT decide compliance, replace verified values, infer fraud, or call an
LLM. Final compliance decisions remain in deterministic rule evaluators.

The current implementation uses in-memory storage because the prototype does
not yet require a production database. The public methods are designed around
shared domain models so a persistent repository can be introduced later
without changing the Evidence/Verification contract.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable, Protocol

from app.evidence.exceptions import (
    DuplicateEvidenceError,
    DuplicateVerificationError,
    EvidenceNotFoundError,
    EvidenceValidationError,
)
from app.models.domain import (
    AuditEvent,
    Bidder,
    ComplianceResult,
    Document,
    Evidence,
    ExtractedField,
    RuleDefinition,
    TenderRequirement,
    Verification,
)


_EVIDENCE_ID_RE = re.compile(r"^EVD-(\d+)$")


class VerificationConnector(Protocol):
    """Minimal connector interface used by verify_and_attach."""

    source_name: str

    def verify(
        self,
        subject: str,
        *,
        evidence_id: str,
        checked_at: datetime | None = None,
    ) -> Verification:
        ...


class EvidenceEngine:
    """Manage evidence records and their verification links in memory.

    The engine owns *evidence lifecycle orchestration*, not compliance logic.
    All records stored here are the exact shared Pydantic domain objects.
    """

    def __init__(
        self,
        evidence: Iterable[Evidence] | None = None,
        verifications: Iterable[Verification] | None = None,
        documents: Iterable[Document] | None = None,
        extracted_fields: Iterable[ExtractedField] | None = None,
    ) -> None:
        self._evidence_by_id: dict[str, Evidence] = {}
        self._verifications_by_id: dict[str, Verification] = {}
        self._evidence_fingerprint_to_id: dict[tuple[Any, ...], str] = {}
        self._source_field_by_evidence_id: dict[str, str] = {}
        self._documents_by_id: dict[str, Document] = {}
        self._extracted_fields_by_id: dict[str, ExtractedField] = {}

        for item in documents or []:
            self.register_document(item)
        for item in extracted_fields or []:
            self.register_extracted_field(item)
        for item in evidence or []:
            self.register_evidence(item)
        for item in verifications or []:
            self.attach_verification(item)

    # ---------------------------------------------------------------------
    # Evidence creation / registration
    # ---------------------------------------------------------------------

    def create_from_extracted_field(
        self,
        *,
        bidder: Bidder,
        requirement: TenderRequirement,
        document: Document,
        extracted_field: ExtractedField,
        evidence_id: str | None = None,
        evidence_type: str = "DOCUMENT_EXTRACT",
        source_label: str | None = None,
        notes: str | None = None,
        deduplicate: bool = True,
    ) -> Evidence:
        """Create an Evidence object from a validated ExtractedField.

        The Evidence value uses ``normalized_value`` when one exists, because
        deterministic rules should consume normalized data. The original
        source phrase remains available through the ExtractedField itself.

        A duplicate is identified by bidder/requirement/document/page/field/
        normalized value. When ``deduplicate=True`` the existing record is
        returned unchanged so a verified record cannot accidentally be
        downgraded by a repeated extraction run.
        """

        self._validate_source_context(
            bidder=bidder,
            requirement=requirement,
            document=document,
            extracted_field=extracted_field,
        )

        value = (
            extracted_field.normalized_value
            if extracted_field.normalized_value is not None
            else extracted_field.value
        )
        fingerprint = self._fingerprint(
            bidder_id=bidder.id,
            requirement_id=requirement.id,
            document_id=document.id,
            page=extracted_field.page,
            field_name=extracted_field.field_name,
            value=value,
        )

        if deduplicate:
            existing_id = self._evidence_fingerprint_to_id.get(fingerprint)
            if existing_id is not None:
                return self._evidence_by_id[existing_id]

        candidate_id = evidence_id or self._next_evidence_id()
        if candidate_id in self._evidence_by_id:
            raise DuplicateEvidenceError(
                f"Evidence ID {candidate_id!r} is already registered."
            )

        evidence = Evidence(
            id=candidate_id,
            bidder_id=bidder.id,
            requirement_id=requirement.id,
            document_id=document.id,
            page=extracted_field.page,
            evidence_type=evidence_type,
            field_name=extracted_field.field_name,
            value=value,
            unit=extracted_field.unit,
            source_label=source_label or document.name,
            confidence=extracted_field.confidence,
            verification_status="UNVERIFIED",
            notes=notes,
        )

        # Keep the source objects available for later evidence-chain assembly.
        self._documents_by_id.setdefault(document.id, document)
        self._extracted_fields_by_id.setdefault(extracted_field.id, extracted_field)
        self.register_evidence(evidence, source_field_id=extracted_field.id)
        if evidence.id not in bidder.evidence_ids:
            bidder.evidence_ids.append(evidence.id)
        return evidence

    def register_document(self, document: Document) -> Document:
        """Register document metadata used by evidence-chain read models."""

        existing = self._documents_by_id.get(document.id)
        if existing is not None:
            if existing != document:
                raise EvidenceValidationError(
                    f"Document ID {document.id!r} is already registered with different data."
                )
            return existing
        self._documents_by_id[document.id] = document
        return document

    def register_extracted_field(self, extracted_field: ExtractedField) -> ExtractedField:
        """Register an extracted field for source-level evidence drill-down."""

        existing = self._extracted_fields_by_id.get(extracted_field.id)
        if existing is not None:
            if existing != extracted_field:
                raise EvidenceValidationError(
                    f"ExtractedField ID {extracted_field.id!r} is already registered "
                    "with different data."
                )
            return existing
        self._extracted_fields_by_id[extracted_field.id] = extracted_field
        return extracted_field

    def get_document(self, document_id: str) -> Document:
        try:
            return self._documents_by_id[document_id]
        except KeyError as exc:
            raise EvidenceNotFoundError(
                f"Document {document_id!r} was not registered in the Evidence Engine."
            ) from exc

    def get_extracted_field(self, extracted_field_id: str) -> ExtractedField:
        try:
            return self._extracted_fields_by_id[extracted_field_id]
        except KeyError as exc:
            raise EvidenceNotFoundError(
                f"Extracted field {extracted_field_id!r} was not registered in the Evidence Engine."
            ) from exc

    def register_evidence(
        self,
        evidence: Evidence,
        *,
        source_field_id: str | None = None,
    ) -> Evidence:
        """Register an existing Evidence object.

        This is useful when bootstrapping the engine from fixtures or when a
        future persistence layer loads existing records.
        """

        if evidence.id in self._evidence_by_id:
            raise DuplicateEvidenceError(
                f"Evidence ID {evidence.id!r} is already registered."
            )

        fingerprint = self._fingerprint(
            bidder_id=evidence.bidder_id,
            requirement_id=evidence.requirement_id,
            document_id=evidence.document_id,
            page=evidence.page,
            field_name=evidence.field_name,
            value=evidence.value,
        )

        self._evidence_by_id[evidence.id] = evidence
        self._evidence_fingerprint_to_id[fingerprint] = evidence.id
        if source_field_id is not None:
            self._source_field_by_evidence_id[evidence.id] = source_field_id
        return evidence

    # ---------------------------------------------------------------------
    # Evidence lookup
    # ---------------------------------------------------------------------

    def get_evidence(self, evidence_id: str) -> Evidence:
        try:
            return self._evidence_by_id[evidence_id]
        except KeyError as exc:
            raise EvidenceNotFoundError(
                f"Evidence {evidence_id!r} was not found."
            ) from exc

    def get_all_evidence(self) -> list[Evidence]:
        """Return evidence in deterministic ID order."""

        return sorted(self._evidence_by_id.values(), key=lambda item: item.id)

    def get_evidence_for_requirement(
        self,
        *,
        bidder_id: str,
        requirement_id: str,
    ) -> list[Evidence]:
        """Return all evidence supporting one bidder/requirement pair."""

        matches = [
            item
            for item in self._evidence_by_id.values()
            if item.bidder_id == bidder_id and item.requirement_id == requirement_id
        ]
        return sorted(matches, key=lambda item: (item.page, item.id))

    def get_evidence_for_document(self, document_id: str) -> list[Evidence]:
        matches = [
            item
            for item in self._evidence_by_id.values()
            if item.document_id == document_id
        ]
        return sorted(matches, key=lambda item: (item.page, item.id))

    # ---------------------------------------------------------------------
    # Verification association
    # ---------------------------------------------------------------------

    def attach_verification(self, verification: Verification) -> Evidence:
        """Register a verification and update the linked Evidence status.

        ``Verification.evidence_id`` is the canonical relationship. The
        Evidence object itself does not gain a verification_id field, keeping
        the shared schema unchanged.
        """

        evidence = self.get_evidence(verification.evidence_id)
        if verification.id in self._verifications_by_id:
            raise DuplicateVerificationError(
                f"Verification ID {verification.id!r} is already registered."
            )

        self._verifications_by_id[verification.id] = verification
        latest = self.get_latest_verification(evidence.id)
        self._evidence_by_id[evidence.id] = evidence.model_copy(
            update={
                "verification_status": (
                    latest.status if latest is not None else evidence.verification_status
                )
            }
        )
        return self._evidence_by_id[evidence.id]

    def verify_and_attach(
        self,
        *,
        evidence_id: str,
        subject: str,
        connector: VerificationConnector,
        checked_at: datetime | None = None,
    ) -> Verification:
        """Call a provider-neutral connector and attach its result to evidence."""

        self.get_evidence(evidence_id)
        verification = connector.verify(
            subject,
            evidence_id=evidence_id,
            checked_at=checked_at,
        )
        if verification.evidence_id != evidence_id:
            raise EvidenceValidationError(
                "Verification connector returned a different evidence_id: "
                f"expected={evidence_id!r}, got={verification.evidence_id!r}."
            )
        self.attach_verification(verification)
        return verification

    def get_verifications_for_evidence(
        self,
        evidence_id: str,
    ) -> list[Verification]:
        """Return every verification attached to one evidence record."""

        self.get_evidence(evidence_id)
        matches = [
            item
            for item in self._verifications_by_id.values()
            if item.evidence_id == evidence_id
        ]
        return sorted(matches, key=lambda item: (item.checked_at, item.id))

    def get_latest_verification(self, evidence_id: str) -> Verification | None:
        verifications = self.get_verifications_for_evidence(evidence_id)
        return verifications[-1] if verifications else None

    def get_all_verifications(self) -> list[Verification]:
        return sorted(
            self._verifications_by_id.values(),
            key=lambda item: (item.checked_at, item.id),
        )

    # ---------------------------------------------------------------------
    # Evidence chain / read model
    # ---------------------------------------------------------------------

    def build_evidence_chain(
        self,
        *,
        requirement: TenderRequirement,
        rule: RuleDefinition,
        compliance_result: ComplianceResult | None = None,
        audit_event: AuditEvent | None = None,
        evidence_ids: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Build a JSON-serializable trace of the evidence supporting a result.

        This is a read model, not a new shared domain entity. It deliberately
        nests the existing objects rather than introducing another competing
        schema. A compliance result and audit event are optional because the
        Evidence Engine can be used before or after deterministic evaluation.
        """

        if evidence_ids is None:
            evidence = self.get_evidence_for_requirement(
                bidder_id=(compliance_result.bidder_id if compliance_result else ""),
                requirement_id=requirement.id,
            ) if compliance_result else [
                item
                for item in self.get_all_evidence()
                if item.requirement_id == requirement.id
            ]
        else:
            evidence = [self.get_evidence(item_id) for item_id in evidence_ids]

        evidence_nodes: list[dict[str, Any]] = []
        for item in evidence:
            verification_records = self.get_verifications_for_evidence(item.id)
            document = self._documents_by_id.get(item.document_id)
            source_field_id = self._source_field_by_evidence_id.get(item.id)
            source_field = (
                self._extracted_fields_by_id.get(source_field_id)
                if source_field_id is not None
                else self._find_matching_extracted_field(item)
            )
            if source_field is not None and source_field_id is None:
                source_field_id = source_field.id

            node: dict[str, Any] = {
                "evidence": item.model_dump(mode="json"),
                "document": (
                    document.model_dump(mode="json")
                    if document is not None
                    else {
                        "document_id": item.document_id,
                        "page": item.page,
                    }
                ),
                "page": item.page,
                "extracted_field": (
                    source_field.model_dump(mode="json")
                    if source_field is not None
                    else None
                ),
                "extracted_value": {
                    "field_name": item.field_name,
                    "value": item.value,
                    "unit": item.unit,
                    "confidence": item.confidence,
                    "source_field_id": source_field_id,
                },
                "verifications": [
                    verification.model_dump(mode="json")
                    for verification in verification_records
                ],
            }
            evidence_nodes.append(node)

        chain: dict[str, Any] = {
            "requirement": requirement.model_dump(mode="json"),
            "rule": rule.model_dump(mode="json"),
            "evidence": evidence_nodes,
        }

        if compliance_result is not None:
            chain["compliance"] = compliance_result.model_dump(mode="json")
        if audit_event is not None:
            chain["audit"] = audit_event.model_dump(mode="json")

        return chain

    # ---------------------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _validate_source_context(
        *,
        bidder: Bidder,
        requirement: TenderRequirement,
        document: Document,
        extracted_field: ExtractedField,
    ) -> None:
        if document.bidder_id != bidder.id:
            raise EvidenceValidationError(
                "Document bidder does not match the supplied bidder: "
                f"document.bidder_id={document.bidder_id!r}, bidder.id={bidder.id!r}."
            )

        if extracted_field.document_id != document.id:
            raise EvidenceValidationError(
                "Extracted field document does not match the supplied document: "
                f"field.document_id={extracted_field.document_id!r}, "
                f"document.id={document.id!r}."
            )

        if not (1 <= extracted_field.page <= document.page_count):
            raise EvidenceValidationError(
                f"Extracted field page {extracted_field.page} is outside "
                f"document page range 1..{document.page_count}."
            )

        if extracted_field.confidence < 0 or extracted_field.confidence > 1:
            raise EvidenceValidationError("Extracted field confidence must be 0..1.")

        if not requirement.id:
            raise EvidenceValidationError("Requirement ID must be non-empty.")

        if not bidder.id:
            raise EvidenceValidationError("Bidder ID must be non-empty.")

    def _find_matching_extracted_field(
        self, evidence: Evidence
    ) -> ExtractedField | None:
        """Best-effort source-field recovery for fixture/persistence bootstrap.

        Evidence does not contain an extracted-field ID in the shared contract.
        When the engine is initialized separately with persisted Evidence and
        ExtractedField records, this method reconnects them using immutable
        source attributes rather than changing the shared schema.
        """

        exact: list[ExtractedField] = []
        fallback: list[ExtractedField] = []
        for field in self._extracted_fields_by_id.values():
            if (
                field.document_id == evidence.document_id
                and field.page == evidence.page
                and field.field_name == evidence.field_name
            ):
                fallback.append(field)
                normalized = (
                    field.normalized_value
                    if field.normalized_value is not None
                    else field.value
                )
                if normalized == evidence.value:
                    exact.append(field)

        if exact:
            return sorted(exact, key=lambda item: item.id)[0]
        if fallback:
            return sorted(fallback, key=lambda item: item.id)[0]
        return None

    @staticmethod
    def _fingerprint(
        *,
        bidder_id: str,
        requirement_id: str,
        document_id: str,
        page: int,
        field_name: str,
        value: Any,
    ) -> tuple[Any, ...]:
        """Produce a stable in-memory deduplication key."""

        try:
            hashable_value = value if hash(value) is not None else repr(value)
        except TypeError:
            hashable_value = repr(value)

        return (
            bidder_id,
            requirement_id,
            document_id,
            page,
            field_name,
            hashable_value,
        )

    def _next_evidence_id(self) -> str:
        highest = 0
        for evidence_id in self._evidence_by_id:
            match = _EVIDENCE_ID_RE.match(evidence_id)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"EVD-{highest + 1:03d}"
