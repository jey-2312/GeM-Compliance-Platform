"""Deterministic compliance orchestration over the prototype rule evaluators."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable

from app.evidence import EvidenceEngine
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
from app.rules.status import STATUS_RULES, evaluate_status_requirement
from app.rules.turnover import evaluate_turnover_requirement


RuleEvaluator = Callable[..., ComplianceResult]


class ComplianceService:
    """Dispatch requirements to deterministic rule evaluators.

    The service has no LLM dependency and does not make decisions from raw
    document text. It receives structured requirements plus Evidence Engine
    records and returns the canonical ComplianceResult object.
    """

    def __init__(self, evaluators: dict[str, RuleEvaluator] | None = None) -> None:
        self._evaluators: dict[str, RuleEvaluator] = {
            "RULE-TURNOVER-GTE": evaluate_turnover_requirement,
            **{rule_id: evaluate_status_requirement for rule_id in STATUS_RULES},
        }
        if evaluators:
            self._evaluators.update(evaluators)

    def supported_rule_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._evaluators))

    def evaluate_requirement(
        self,
        *,
        requirement: TenderRequirement,
        bidder: Bidder,
        evidence_engine: EvidenceEngine,
        result_id: str,
        finding_ids: list[str] | None = None,
        evaluated_at: datetime | None = None,
    ) -> ComplianceResult:
        """Evaluate one requirement using only evidence already in the engine."""

        evaluator = self._evaluators.get(requirement.rule_id)
        if evaluator is None:
            # Unsupported/unclear requirements remain visible to the officer.
            # They are never silently treated as FAIL and never evaluated by an LLM.
            return ComplianceResult(
                id=result_id,
                tender_id=requirement.tender_id,
                bidder_id=bidder.id,
                requirement_id=requirement.id,
                status="MANUAL_REVIEW",
                rule_id=requirement.rule_id,
                expected=requirement.threshold,
                actual=None,
                evidence_ids=[
                    item.id
                    for item in evidence_engine.get_evidence_for_requirement(
                        bidder_id=bidder.id,
                        requirement_id=requirement.id,
                    )
                ],
                finding_ids=list(finding_ids or []),
                explanation=(
                    "No deterministic evaluator is registered for this requirement; "
                    "manual review is required."
                ),
                evaluated_at=evaluated_at or datetime.now(timezone.utc),
            )

        evidence = evidence_engine.get_evidence_for_requirement(
            bidder_id=bidder.id,
            requirement_id=requirement.id,
        )
        verifications = [
            verification
            for evidence_item in evidence
            for verification in evidence_engine.get_verifications_for_evidence(
                evidence_item.id
            )
        ]

        return evaluator(
            requirement,
            evidence,
            verifications,
            bidder_id=bidder.id,
            result_id=result_id,
            evaluated_at=evaluated_at,
            finding_ids=finding_ids,
        )

    @staticmethod
    def audit_event_for(
        result: ComplianceResult,
        *,
        audit_id: str,
        timestamp: datetime | None = None,
        details: str = "Deterministic rule evaluated against verified evidence.",
    ) -> AuditEvent:
        """Create the canonical audit event corresponding to one result."""

        return AuditEvent(
            id=audit_id,
            timestamp=timestamp or result.evaluated_at or datetime.now(timezone.utc),
            actor_type="SYSTEM",
            action="COMPLIANCE_EVALUATED",
            tender_id=result.tender_id,
            bidder_id=result.bidder_id,
            requirement_id=result.requirement_id,
            rule_id=result.rule_id,
            result_id=result.id,
            details=details,
        )

    @staticmethod
    def rule_definition_for(requirement: TenderRequirement) -> RuleDefinition:
        """Return the canonical RuleDefinition used for evidence-chain display."""

        rule_id = requirement.rule_id
        if rule_id == "RULE-TURNOVER-GTE":
            return RuleDefinition(
                id=rule_id,
                type="NUMERIC_COMPARISON",
                field="average_annual_turnover",
                operator="GREATER_THAN_OR_EQUAL",
                threshold_source="requirement.threshold",
                mandatory=requirement.mandatory,
                version="1.0",
            )

        status_rule = STATUS_RULES.get(rule_id)
        if status_rule is not None:
            return RuleDefinition(
                id=rule_id,
                type="STATUS_COMPARISON",
                field=status_rule["field"],
                operator="STATUS_ACTIVE",
                threshold_source=f"required_status:{status_rule['expected']}",
                mandatory=requirement.mandatory,
                version="1.0",
            )

        raise ValueError(f"No RuleDefinition factory is registered for {rule_id!r}.")
