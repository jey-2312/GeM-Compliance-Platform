"""Application state factory for the in-memory prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.workflow_service import WorkflowService
from app.verification.service import VerificationService


@dataclass
class AppState:
    workflow: WorkflowService
    verification: VerificationService
    officer_events: list[dict[str, Any]] = field(default_factory=list)
    reviewed_tenders_by_bidder: dict[str, list[str]] = field(default_factory=dict)


def build_default_state() -> AppState:
    repo_root = Path(__file__).resolve().parents[3]
    fixtures_dir = repo_root / "data" / "fixtures"
    return AppState(
        workflow=WorkflowService.from_fixtures(fixtures_dir),
        verification=VerificationService(mode="mock"),
    )
