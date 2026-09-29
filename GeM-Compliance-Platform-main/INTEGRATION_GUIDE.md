# Frontend ↔ FastAPI Integration Guide

This prototype uses one backend as the source of truth.

```text
React / Vite
    │
    │ /api/v1/*
    ▼
FastAPI
    │
    ├── WorkflowService
    ├── Evidence Engine
    ├── Mock Verification
    └── Deterministic Rule Engine
    │
    ▼
ComplianceResult + Evidence Chain + Audit
    │
    ▼
React dashboard / drill-down / officer review
```

## What is connected

The frontend now reads tenders and requirements from FastAPI, evaluates compliance through FastAPI, reads the bidder passport from FastAPI, reads evidence chains from FastAPI, runs mock verification through FastAPI, loads audit history from FastAPI, and sends officer dispositions back to FastAPI.

The old standalone Express frontend server and frontend-side compliance calculations are removed from the runtime path. `frontend/src/data/procurementData.ts` was also removed because it duplicated the backend domain model and could drift from the canonical contract.

## Local run on Windows PowerShell

Open terminal 1 at the repository root:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
& ".\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

If your virtual environment is in another location, replace the Python executable path. The important part is that `PYTHONPATH` contains both the repository root and `backend`.

Check:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/docs
```

Open terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://localhost:5173
```

Vite proxies `/api/*` to `http://127.0.0.1:8000`, so the browser talks to the same-origin Vite URL while FastAPI remains the API server.

## Environment variables

Root `.env.example`:

```text
LLM_API_KEY=
LLM_MODEL=openai/gpt-oss-20b
BACKEND_URL=
VERIFICATION_PROVIDER_MODE=mock
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Frontend `.env.example`:

```text
VITE_API_BASE_URL=/api/v1
VITE_PROJECT_NAME=PS26100 Procurement Audit Platform
```

Do not commit real keys or credentials.

## Canonical frontend flow

### 1. Tender Requirements

The page calls:

```text
GET /api/v1/tenders
GET /api/v1/tenders/{tender_id}
GET /api/v1/tenders/{tender_id}/requirements
```

The UI maps backend fields into display-only properties such as `threshold_display` and `citation_page`. It does not evaluate compliance.

`POST /api/v1/tenders/{tender_id}/extract` supports two modes:

- default: reload the frozen canonical fixture
- `?live=true`: run the real PyMuPDF → LLM → structured extraction path against the sample Tender PDF; this requires `LLM_API_KEY`

Live extraction is deliberately returned as a preview so one LLM failure cannot corrupt the frozen Tender A/B demo dataset.

### 2. Bidder Passport

The page calls:

```text
GET /api/v1/bidders/{bidder_id}/passport
POST /api/v1/bidders/{bidder_id}/verify
```

The passport is reusable bidder evidence. The tender determines the current compliance outcome.

Verification is explicitly mock in this prototype.

### 3. Compliance Matrix

The page calls:

```text
POST /api/v1/compliance/evaluate
```

The response drives all status/count displays. No compliance arithmetic is performed in React.

For the seeded demo:

- Tender A: ₹4.8 Cr verified turnover vs ₹5 Cr requirement → `FAIL`
- GST → `PASS`
- PAN → `PASS`
- Udyam → `PASS`
- Tender B: ₹4.8 Cr verified turnover vs ₹3 Cr requirement → `PASS`

### 4. Evidence Drill-Down

The matrix passes backend evidence/result identifiers into the evidence viewer. Detailed evidence is available through:

```text
GET /api/v1/evidence/{evidence_id}
GET /api/v1/evidence/{evidence_id}/verifications
GET /api/v1/evidence/{evidence_id}/chain
```

The chain shown to an officer is:

```text
Requirement
→ Rule
→ Evidence
→ Document / Page
→ Extracted Value
→ Verification
→ Compliance Result
→ Audit
```

### 5. Contradiction + officer review

The page derives the turnover contradiction from backend evidence and calls:

```text
POST /api/v1/ai/explain-contradiction
POST /api/v1/ai/draft-clarification
POST /api/v1/audit/commit
GET  /api/v1/audit/{tender_id}/{bidder_id}
```

The officer action is recorded by the backend and the SHA-256 audit hash is generated server-side.

The system records the self-declared ₹6.2 Cr and audited/verified ₹4.8 Cr discrepancy for review. It does not label the discrepancy as fraud automatically.

## Recommended demo sequence

1. Start FastAPI.
2. Start Vite.
3. Open Tender A.
4. Show the four backend-provided requirements and source page 7.
5. Open Bidder Passport.
6. Show the self-declared ₹6.2 Cr and audited/verified ₹4.8 Cr evidence.
7. Open Compliance Matrix and run the backend rule engine.
8. Show `FAIL 1 / PASS 3` for Tender A.
9. Open the turnover evidence drill-down.
10. Show document/page, value, verification source, rule ID and compliance result.
11. Open Compliance & Contradictions.
12. Show the discrepancy finding and manual-review wording.
13. Generate the factual explanation and/or clarification draft.
14. Record an officer disposition.
15. Switch to Tender B.
16. Run the rule engine again and show the same bidder's turnover result becomes `PASS` because the tender threshold is ₹3 Cr.
17. Show the accumulated audit/activity history.

## Optional live AI demonstration

For the separate upload button:

1. Set the backend `LLM_API_KEY`.
2. Start/restart FastAPI after setting the key.
3. In Tender Requirements, choose **Upload for AI Preview**.
4. Upload a PDF or plain-text tender.
5. The file is sent to `POST /api/v1/documents/ocr-process`.
6. PDF text extraction uses PyMuPDF first.
7. The structured LLM output is validated through the backend requirement adapter.
8. The response is preview-only and does not replace the seeded Tender A/B state.

OCR fallback remains isolated because the development specification explicitly makes OCR non-critical-path for the prototype.

## What not to do

Do not add another Express API, duplicate the canonical compliance calculations in React, treat mock verification as a live government integration, or let uploaded document text act as executable instructions.

Do not change the shared field names without updating the canonical backend schema first and then its consumers.

## Validation completed on the packaged repo

Backend tests pass with:

```bash
PYTHONPATH="$PWD:$PWD/backend" python -m pytest -q
```

The packaged frontend source has also been checked for TypeScript/TSX parsing, and a temporary type-check run with external React/Lucide type stubs completed without source-level type errors. A production Vite bundle was not built inside this environment because the frontend dependency installation requires npm package downloads.
