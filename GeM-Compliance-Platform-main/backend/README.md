# Backend Prototype

This backend contains the shared domain contract and the deterministic pieces
of the SIH 26100 GeM compliance prototype.

## Included

- Pydantic shared domain contract
- Synthetic seed fixtures
- AI → backend requirement adapter
- Deterministic rule evaluators
- Provider-neutral verification connectors with mock GST/PAN/Udyam/financial sources
- Evidence Engine and evidence-chain read model
- End-to-end compliance workflow service
- ComplianceResult + AuditEvent orchestration
- FastAPI HTTP API over the application services
- API Setu-ready provider boundary without inventing live provider contracts
- Automated backend + AI integration tests

## Architecture

```text
AI / document intelligence
        ↓
TenderRequirement / ExtractedField
        ↓
Evidence Engine
        ↓
Mock or authorized VerificationConnector
        ↓
Deterministic Rule Engine
        ↓
ComplianceResult
        ↓
Evidence Chain + AuditEvent
        ↓
FastAPI
        ↓
Frontend
```

## Run tests

From repository root:

```powershell
python -m pytest -q
```

## Run API

From repository root:

```powershell
$env:PYTHONPATH="backend;."
python -m uvicorn app.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

The current prototype remains in-memory and fixture-backed. Production
persistence, production RBAC, and live government integrations are outside
the prototype critical path.
