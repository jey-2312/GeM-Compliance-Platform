"""Command-line demonstration of the complete fixture-backed workflow."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.workflow_service import WorkflowService


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    service = WorkflowService.from_fixtures(project_root / "data" / "fixtures")
    reports = service.run_both_demo_tenders(
        bidder_id="BIDDER-001",
        evaluated_at=datetime.now(timezone.utc),
    )

    for tender_id, report in reports.items():
        print(f"\n=== {tender_id}: {report['tender']['title']} ===")
        print(f"Bidder: {report['bidder']['legal_name']}")
        print(f"Summary: {report['summary']}")

        for result in report["compliance_results"]:
            print(
                f"  {result['requirement_id']}: {result['status']} "
                f"(actual={result['actual']!r}, expected={result['expected']!r}, "
                f"evidence={result['evidence_ids']})"
            )

        turnover_result = next(
            item
            for item in report["compliance_results"]
            if item["requirement_id"] in {"REQ-001", "REQ-005"}
        )
        chain = report["evidence_chains"][turnover_result["id"]]
        print("  Turnover evidence chain:")
        print(json.dumps(chain, indent=2))


if __name__ == "__main__":
    main()
