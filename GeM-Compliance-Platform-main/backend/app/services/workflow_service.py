"""End-to-end in-memory compliance workflow for the prototype.

This service wires together the already implemented components without adding
an HTTP server or database. It is intentionally fixture-friendly for local
integration testing and has injectable boundaries for the real AI layer.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from ai.extraction.contradiction_detector import detect_contradictions
from ai.schemas.models import ContradictionFinding

from app.evidence import EvidenceEngine
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
from app.rules.status import STATUS_RULES
from app.services.compliance_service import ComplianceService
from app.services.seed_loader import load_all_fixtures
from app.verification import (
    MockFinancialVerificationConnector,
    MockGSTConnector,
    MockOEMConnector,
    MockPANConnector,
    MockUdyamConnector,
)


_FINDING_FOR_FIELD = {
    "average_annual_turnover": "turnover",
}
_EVD_ID_RE = re.compile(r"^EVD-(\d+)$")


class WorkflowService:
    """Coordinate one complete bidder/tender compliance evaluation in memory."""

    def __init__(
        self,
        *,
        tenders: Iterable[Tender],
        requirements: Iterable[TenderRequirement],
        bidders: Iterable[Bidder],
        documents: Iterable[Document],
        extracted_fields: Iterable[ExtractedField],
        rules: Iterable[RuleDefinition],
        evidence_engine: EvidenceEngine | None = None,
        contradiction_detector: Callable[..., list[ContradictionFinding]] = detect_contradictions,
        compliance_service: ComplianceService | None = None,
    ) -> None:
        self._tenders = {item.id: item for item in tenders}
        self._requirements = {item.id: item for item in requirements}
        self._bidders = {item.id: item for item in bidders}
        self._documents = {item.id: item for item in documents}
        self._extracted_fields = {item.id: item for item in extracted_fields}
        self._rules = {item.id: item for item in rules}
        self._evidence_engine = evidence_engine or EvidenceEngine(
            documents=documents,
            extracted_fields=extracted_fields,
        )
        self._compliance_service = compliance_service or ComplianceService()
        self._contradiction_detector = contradiction_detector
        self._results: dict[str, ComplianceResult] = {}
        self._audits: dict[str, AuditEvent] = {}
        self._findings: dict[str, ContradictionFinding] = {}

    @classmethod
    def from_fixtures(cls, fixtures_dir: str | Path) -> "WorkflowService":
        """Build a workflow service from the canonical synthetic fixtures."""

        loaded = load_all_fixtures(Path(fixtures_dir))
        engine = EvidenceEngine(
            documents=loaded["documents.json"],
            extracted_fields=loaded["extracted_fields.json"],
            evidence=loaded["evidence.json"],
            verifications=loaded["verifications.json"],
        )
        return cls(
            tenders=loaded["tenders.json"],
            requirements=loaded["requirements.json"],
            bidders=loaded["bidders.json"],
            documents=loaded["documents.json"],
            extracted_fields=loaded["extracted_fields.json"],
            rules=loaded["rules.json"],
            evidence_engine=engine,
        )

    @property
    def evidence_engine(self) -> EvidenceEngine:
        return self._evidence_engine

    def get_tender(self, tender_id: str) -> Tender:
        try:
            return self._tenders[tender_id]
        except KeyError as exc:
            raise ValueError(f"Unknown tender_id={tender_id!r}.") from exc

    def get_bidder(self, bidder_id: str) -> Bidder:
        try:
            return self._bidders[bidder_id]
        except KeyError as exc:
            raise ValueError(f"Unknown bidder_id={bidder_id!r}.") from exc

    def get_requirements_for_tender(self, tender_id: str) -> list[TenderRequirement]:
        tender = self.get_tender(tender_id)
        requirements: list[TenderRequirement] = []
        for requirement_id in tender.requirements:
            try:
                requirement = self._requirements[requirement_id]
            except KeyError as exc:
                raise ValueError(
                    f"Tender {tender_id!r} references unknown requirement {requirement_id!r}."
                ) from exc
            if requirement.tender_id != tender_id:
                raise ValueError(
                    f"Requirement {requirement.id!r} belongs to {requirement.tender_id!r}, "
                    f"not tender {tender_id!r}."
                )
            requirements.append(requirement)
        return requirements

    def run(
        self,
        *,
        tender_id: str,
        bidder_id: str,
        evaluated_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Run the complete fixture-backed evidence/compliance workflow."""

        tender = self.get_tender(tender_id)
        bidder = self.get_bidder(bidder_id)
        requirements = self.get_requirements_for_tender(tender_id)
        timestamp = evaluated_at or datetime.now(timezone.utc)

        self._ensure_requirement_evidence(bidder, requirements)
        passport_verifications = self._verify_passport(bidder, timestamp)
        self._verify_tender_status_evidence(bidder, requirements, timestamp)
        self._verify_turnover_evidence(bidder, requirements, timestamp)

        findings = self._detect_bidder_contradictions(bidder)
        for finding in findings:
            self._findings[finding.finding_id] = finding

        results: list[ComplianceResult] = []
        audits: list[AuditEvent] = []
        chains: dict[str, dict[str, Any]] = {}

        for index, requirement in enumerate(requirements, start=1):
            requirement_findings = self._finding_ids_for_requirement(requirement, findings)
            result_id = self._result_id(tender_id, bidder_id, requirement.id, index)
            result = self._compliance_service.evaluate_requirement(
                requirement=requirement,
                bidder=bidder,
                evidence_engine=self._evidence_engine,
                result_id=result_id,
                finding_ids=requirement_findings,
                evaluated_at=timestamp,
            )
            audit_id = self._audit_id(tender_id, bidder_id, requirement.id)
            audit = self._compliance_service.audit_event_for(
                result,
                audit_id=audit_id,
                timestamp=result.evaluated_at,
            )

            rule = self._rule_for(requirement)
            chain = self._evidence_engine.build_evidence_chain(
                requirement=requirement,
                rule=rule,
                compliance_result=result,
                audit_event=audit,
                evidence_ids=result.evidence_ids,
            )

            self._results[result.id] = result
            self._audits[audit.id] = audit
            results.append(result)
            audits.append(audit)
            chains[result.id] = chain

        summary = Counter(result.status.value for result in results)

        tender_evidence = self._evidence_for_tender_bidder(tender_id, bidder_id)
        tender_verifications = [
            verification
            for evidence in tender_evidence
            for verification in self._evidence_engine.get_verifications_for_evidence(
                evidence.id
            )
        ]

        return {
            "tender": tender.model_dump(mode="json"),
            "bidder": bidder.model_dump(mode="json"),
            "requirements": [item.model_dump(mode="json") for item in requirements],
            "passport_verifications": [
                item.model_dump(mode="json") for item in passport_verifications
            ],
            "findings": [item.model_dump(mode="json") for item in findings],
            "evidence": [item.model_dump(mode="json") for item in tender_evidence],
            "verifications": [
                item.model_dump(mode="json") for item in sorted(
                    tender_verifications,
                    key=lambda value: (value.checked_at, value.id),
                )
            ],
            "compliance_results": [item.model_dump(mode="json") for item in results],
            "audit_events": [item.model_dump(mode="json") for item in audits],
            "evidence_chains": chains,
            "summary": dict(summary),
        }

    def run_both_demo_tenders(
        self,
        *,
        bidder_id: str,
        evaluated_at: datetime | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Run the two canonical demo tenders for one bidder."""

        return {
            tender_id: self.run(
                tender_id=tender_id,
                bidder_id=bidder_id,
                evaluated_at=evaluated_at,
            )
            for tender_id in self._tenders
        }

    def list_tenders(self) -> list[Tender]:
        """Return tenders in deterministic ID order."""

        return sorted(self._tenders.values(), key=lambda item: item.id)

    def list_bidders(self) -> list[Bidder]:
        """Return bidders in deterministic ID order."""

        return sorted(self._bidders.values(), key=lambda item: item.id)

    def get_results(self, tender_id: str, bidder_id: str) -> list[ComplianceResult]:
        """Return stored compliance results for one tender/bidder pair."""

        self.get_tender(tender_id)
        self.get_bidder(bidder_id)
        return sorted(
            [
                result
                for result in self._results.values()
                if result.tender_id == tender_id and result.bidder_id == bidder_id
            ],
            key=lambda item: (item.evaluated_at, item.id),
        )

    def get_result(self, result_id: str) -> ComplianceResult:
        try:
            return self._results[result_id]
        except KeyError as exc:
            raise ValueError(f"Unknown result_id={result_id!r}.") from exc

    def get_result_bundle(self, result_id: str) -> dict[str, Any]:
        """Return one result plus its evidence, verifications, audit and chain."""

        result = self.get_result(result_id)
        requirement = self._requirements.get(result.requirement_id)
        if requirement is None:
            raise ValueError(
                f"Result {result.id!r} references unknown requirement {result.requirement_id!r}."
            )
        rule = self._rule_for(requirement)
        audit = next(
            (item for item in self._audits.values() if item.result_id == result.id),
            None,
        )
        if audit is None:
            raise ValueError(f"No audit event is stored for result {result.id!r}.")

        evidence = [
            self._evidence_engine.get_evidence(evidence_id)
            for evidence_id in result.evidence_ids
        ]
        verifications = [
            verification
            for evidence_item in evidence
            for verification in self._evidence_engine.get_verifications_for_evidence(
                evidence_item.id
            )
        ]
        chain = self._evidence_engine.build_evidence_chain(
            requirement=requirement,
            rule=rule,
            compliance_result=result,
            audit_event=audit,
            evidence_ids=result.evidence_ids,
        )
        return {
            "result": result,
            "evidence": evidence,
            "verifications": sorted(
                verifications, key=lambda item: (item.checked_at, item.id)
            ),
            "audit_events": [audit],
            "evidence_chain": chain,
        }

    def get_evidence_chain_for_evidence(self, evidence_id: str) -> dict[str, Any]:
        """Return the most recent stored result chain that contains an evidence ID."""

        self._evidence_engine.get_evidence(evidence_id)
        candidate_results = [
            result
            for result in self._results.values()
            if evidence_id in result.evidence_ids
        ]
        if not candidate_results:
            raise ValueError(
                f"No evaluated compliance result currently references evidence {evidence_id!r}."
            )
        selected = sorted(
            candidate_results, key=lambda item: (item.evaluated_at, item.id), reverse=True
        )[0]
        bundle = self.get_result_bundle(selected.id)
        return bundle["evidence_chain"]

    def get_audit_history(self, tender_id: str, bidder_id: str) -> list[AuditEvent]:
        return sorted(
            [
                event
                for event in self._audits.values()
                if event.tender_id == tender_id and event.bidder_id == bidder_id
            ],
            key=lambda item: (item.timestamp, item.id),
        )

    def _ensure_requirement_evidence(
        self,
        bidder: Bidder,
        requirements: Iterable[TenderRequirement],
    ) -> None:
        """Ensure each demo requirement has tender-specific evidence records."""

        for requirement in requirements:
            existing = self._evidence_engine.get_evidence_for_requirement(
                bidder_id=bidder.id,
                requirement_id=requirement.id,
            )
            if existing:
                continue

            if requirement.type == "TURNOVER":
                turnover_fields = [
                    field
                    for field in self._extracted_fields.values()
                    if field.field_name == "average_annual_turnover"
                ]
                for field in sorted(turnover_fields, key=lambda item: (item.page, item.id)):
                    document = self._documents[field.document_id]
                    self._evidence_engine.create_from_extracted_field(
                        bidder=bidder,
                        requirement=requirement,
                        document=document,
                        extracted_field=field,
                        deduplicate=True,
                    )
                continue

            if requirement.rule_id == "RULE-MANUAL-REVIEW":
                continue

            field_name = self._field_name_for_status_requirement(requirement)
            template = self._find_passport_evidence(bidder.id, field_name)
            if template is None:
                continue
            cloned = self._clone_evidence_for_requirement(template, requirement)
            self._evidence_engine.register_evidence(cloned)

    def _verify_tender_status_evidence(
        self,
        bidder: Bidder,
        requirements: Iterable[TenderRequirement],
        checked_at: datetime,
    ) -> None:
        """Verify status evidence attached to the current tender requirements."""

        connector_by_field = {
            "gst_status": MockGSTConnector(),
            "pan_status": MockPANConnector(),
            "udyam_status": MockUdyamConnector(),
            "oem_authorization_status": MockOEMConnector(),
        }
        subject_by_field = {
            "gst_status": bidder.gstin,
            "pan_status": bidder.pan,
            "udyam_status": bidder.udyam,
            "oem_authorization_status": bidder.id,
        }

        for requirement in requirements:
            if requirement.rule_id not in STATUS_RULES:
                continue
            field_name = self._field_name_for_status_requirement(requirement)
            connector = connector_by_field[field_name]
            subject = subject_by_field[field_name]
            evidence = self._find_tender_evidence(
                bidder.id, requirement.id, field_name
            )
            if evidence is None:
                continue

            latest = self._evidence_engine.get_latest_verification(evidence.id)
            if latest is None or latest.status != "VERIFIED" or latest.verified_value is None:
                self._evidence_engine.verify_and_attach(
                    evidence_id=evidence.id,
                    subject=subject,
                    connector=connector,
                    checked_at=checked_at,
                )

    def _verify_turnover_evidence(
        self,
        bidder: Bidder,
        requirements: Iterable[TenderRequirement],
        checked_at: datetime,
    ) -> None:
        """Verify audited turnover evidence for every tender turnover requirement."""

        connector = MockFinancialVerificationConnector()
        for requirement in requirements:
            if requirement.type != "TURNOVER":
                continue

            candidates = self._evidence_engine.get_evidence_for_requirement(
                bidder_id=bidder.id,
                requirement_id=requirement.id,
            )
            audited = []
            for item in candidates:
                document = self._documents.get(item.document_id)
                if document is not None and document.document_type == "AUDITED_FINANCIALS":
                    audited.append(item)

            if not audited:
                continue

            evidence = sorted(audited, key=lambda item: (item.page, item.id))[0]
            latest = self._evidence_engine.get_latest_verification(evidence.id)
            if latest is None or latest.status != "VERIFIED" or latest.verified_value is None:
                self._evidence_engine.verify_and_attach(
                    evidence_id=evidence.id,
                    subject=bidder.id,
                    connector=connector,
                    checked_at=checked_at,
                )

    def _verify_passport(
        self,
        bidder: Bidder,
        checked_at: datetime,
    ) -> list[Verification]:
        """Verify identity/registration evidence through the mock connectors."""

        connectors = (
            ("gst_status", bidder.gstin, MockGSTConnector()),
            ("pan_status", bidder.pan, MockPANConnector()),
            ("udyam_status", bidder.udyam, MockUdyamConnector()),
        )
        verifications: list[Verification] = []

        for field_name, subject, connector in connectors:
            evidence = self._find_passport_evidence(bidder.id, field_name)
            if evidence is None:
                continue
            latest = self._evidence_engine.get_latest_verification(evidence.id)
            if latest is None or latest.status != "VERIFIED" or latest.verified_value is None:
                verification = self._evidence_engine.verify_and_attach(
                    evidence_id=evidence.id,
                    subject=subject,
                    connector=connector,
                    checked_at=checked_at,
                )
            else:
                verification = latest
            verifications.append(verification)

        return verifications

    def _detect_bidder_contradictions(
        self,
        bidder: Bidder,
    ) -> list[ContradictionFinding]:
        fields = [
            field
            for field in self._extracted_fields.values()
            if self._document_for(field.document_id).bidder_id == bidder.id
        ]
        document_types = {
            document.id: document.document_type for document in self._documents.values()
        }
        document_names = {
            document.id: document.name for document in self._documents.values()
        }
        return self._contradiction_detector(
            fields,
            document_types=document_types,
            document_names=document_names,
        )

    def _finding_ids_for_requirement(
        self,
        requirement: TenderRequirement,
        findings: Iterable[ContradictionFinding],
    ) -> list[str]:
        field_name = {
            "TURNOVER": "average_annual_turnover",
        }.get(requirement.type)
        if field_name is None:
            return []
        return [finding.finding_id for finding in findings if finding.field_name == field_name]

    def _rule_for(self, requirement: TenderRequirement) -> RuleDefinition:
        rule = self._rules.get(requirement.rule_id)
        if rule is not None:
            return rule
        return self._compliance_service.rule_definition_for(requirement)

    def _evidence_for_tender_bidder(self, tender_id: str, bidder_id: str) -> list[Evidence]:
        requirement_ids = {item.id for item in self.get_requirements_for_tender(tender_id)}
        return sorted(
            [
                item
                for item in self._evidence_engine.get_all_evidence()
                if item.bidder_id == bidder_id and item.requirement_id in requirement_ids
            ],
            key=lambda item: (item.requirement_id, item.page, item.id),
        )

    def _find_tender_evidence(
        self, bidder_id: str, requirement_id: str, field_name: str
    ) -> Evidence | None:
        candidates = [
            item
            for item in self._evidence_engine.get_all_evidence()
            if item.bidder_id == bidder_id
            and item.requirement_id == requirement_id
            and item.field_name == field_name
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: (item.page, item.id))[0]

    def _find_passport_evidence(self, bidder_id: str, field_name: str) -> Evidence | None:
        candidates = [
            item
            for item in self._evidence_engine.get_all_evidence()
            if item.bidder_id == bidder_id and item.field_name == field_name
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item.id)[0]

    def _clone_evidence_for_requirement(
        self,
        template: Evidence,
        requirement: TenderRequirement,
    ) -> Evidence:
        next_id = self._next_evidence_id()
        return template.model_copy(
            update={
                "id": next_id,
                "requirement_id": requirement.id,
                "verification_status": "UNVERIFIED",
                "notes": (
                    template.notes
                    or ""
                )
                + " Reused from the bidder's evidence passport for this tender requirement.",
            }
        )

    def _next_evidence_id(self) -> str:
        highest = 0
        for evidence in self._evidence_engine.get_all_evidence():
            match = _EVD_ID_RE.match(evidence.id)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"EVD-{highest + 1:03d}"

    def _document_for(self, document_id: str) -> Document:
        try:
            return self._documents[document_id]
        except KeyError as exc:
            raise ValueError(f"Unknown document_id={document_id!r}.") from exc

    @staticmethod
    def _field_name_for_status_requirement(requirement: TenderRequirement) -> str:
        mapping = {
            "RULE-GST-ACTIVE": "gst_status",
            "RULE-PAN-VALID": "pan_status",
            "RULE-UDYAM-ACTIVE": "udyam_status",
            "RULE-OEM-AUTHORIZATION-ACTIVE": "oem_authorization_status",
        }
        try:
            return mapping[requirement.rule_id]
        except KeyError as exc:
            raise ValueError(
                f"No evidence-field mapping exists for {requirement.rule_id!r}."
            ) from exc

    @staticmethod
    def _result_id(tender_id: str, bidder_id: str, requirement_id: str, index: int) -> str:
        return f"CMP-RUN-{tender_id}-{bidder_id}-{index:03d}"

    @staticmethod
    def _audit_id(tender_id: str, bidder_id: str, requirement_id: str) -> str:
        return f"AUD-RUN-{tender_id}-{bidder_id}-{requirement_id}"
