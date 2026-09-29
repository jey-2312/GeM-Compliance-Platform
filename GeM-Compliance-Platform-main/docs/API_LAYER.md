# Prototype API Layer

The FastAPI layer is intentionally thin. It exposes the already-implemented
workflow, evidence, verification, and audit services over HTTP. Business
rules stay in application services and deterministic rule evaluators.

## Run locally

From the repository root:

### Windows PowerShell

```powershell
$env:PYTHONPATH="backend;."
python -m uvicorn app.main:app --reload
```

### Windows CMD

```cmd
set PYTHONPATH=backend;.
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## API surface

All endpoints are under `/api/v1`.

### System

- `GET /health`

### Tenders

- `GET /tenders`
- `GET /tenders/{tender_id}`
- `GET /tenders/{tender_id}/requirements`

### Bidders

- `GET /bidders`
- `GET /bidders/{bidder_id}`
- `GET /bidders/{bidder_id}/evidence`

### Compliance

- `POST /compliance/evaluate`
- `GET /compliance/results/{result_id}`
- `GET /compliance/{tender_id}/{bidder_id}/results`
- `GET /compliance/{tender_id}/{bidder_id}/audit`

### Evidence

- `GET /evidence/{evidence_id}`
- `GET /evidence/{evidence_id}/verifications`
- `GET /evidence/{evidence_id}/chain`

### Verification

- `GET /verification/providers`
- `POST /verification/verify`

The current configuration exposes deterministic mock GST, PAN, Udyam and
financial verification. The API Setu boundary is provider-neutral: no
provider-specific live endpoint or payload is guessed or hard-coded.

## Evaluate a bidder

Request:

```json
{
  "tender_id": "TND-001",
  "bidder_id": "BIDDER-001"
}
```

The endpoint runs the existing workflow service and returns the tender,
bidder, requirements, findings, evidence, verifications, compliance results,
audit events, evidence chains, and summary.

For the canonical fixture data, Tender A produces a turnover `FAIL` because
verified turnover is ₹4.8 crore against a ₹5 crore threshold. Tender B can be
run with the same bidder and produces a turnover `PASS` against its ₹3 crore
threshold.

## Verification request

```json
{
  "kind": "gst",
  "subject": "29ABCDE1234F1Z5",
  "evidence_id": "EVD-003"
}
```

The result is the shared `Verification` object. The endpoint then attaches
that verification to the evidence record through the existing Evidence Engine.

## API Setu integration boundary

Do not place real API Setu credentials in source code. The repository contains
`backend/app/verification/api_setu.py`, an abstract HTTP boundary for an
approved provider adapter.

API Setu's current material states that consumers must obtain access/approval,
subscribe to the required API, and use the endpoint and request/response
contract provided by the specific API documentation. Its published SOP also
describes Client ID + API Key headers for the standard key-based flow while
noting that some APIs can use different authentication. See the official
API Setu SOP and marketplace documentation before implementing a concrete
provider adapter.
