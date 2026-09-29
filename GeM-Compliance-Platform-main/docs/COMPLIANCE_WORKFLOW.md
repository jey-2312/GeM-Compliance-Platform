# Compliance Workflow Service

The prototype workflow service connects the existing AI/domain, Evidence Engine,
mock verification, deterministic rules, contradiction finding, ComplianceResult,
and AuditEvent pieces without adding a database or HTTP layer.

## Flow

```text
Tender + Bidder
    ↓
Requirement-specific evidence
    ↓
Mock passport/financial verification
    ↓
Contradiction detection
    ↓
Deterministic rule evaluation
    ↓
ComplianceResult
    ↓
Evidence chain + AuditEvent
```

## Run locally

From the repository root:

```powershell
$env:PYTHONPATH="backend;ai"
python -c "from pathlib import Path; from backend.app.services.workflow_service import WorkflowService"
```

The automated integration test uses the canonical fixtures in `data/fixtures`.

## Demo behavior

For `BIDDER-001`:

- Tender A: turnover ₹4.8 Cr vs ₹5 Cr → `FAIL`.
- Tender B: turnover ₹4.8 Cr vs ₹3 Cr → `PASS`.
- GST, PAN, and Udyam are checked through the existing mock verification connectors.
- The ₹6.2 Cr self-declaration remains separate evidence and produces a discrepancy finding against the audited ₹4.8 Cr value.

Mock sources remain explicitly identified as mock; no live government connection is claimed.
