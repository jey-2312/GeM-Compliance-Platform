# GeM Compliance Platform

AI-assisted bid compliance verification prototype for SIH 26100.

## Core Principle

AI understands → Code verifies → Evidence explains → Officer decides

## Documentation

### Primary Implementation Specification

[DEVELOPMENT_SPEC.md](./DEVELOPMENT_SPEC.md)

This is the source of truth for prototype coding and integration.

### Project Context

Supporting documents are available in:

`project-context/`

These provide product, team, and long-term context but do not override
the Development Specification.

## Project Structure

- `frontend/` — Frontend application
- `backend/` — FastAPI backend, rules, evidence, verification
- `ai/` — AI/document intelligence, field extraction, contradiction checks, explanations
- `data/` — Fixtures, bidders, tenders, mock sources
- `docs/` — Schemas and technical documentation
- `project-context/` — Supporting project documents

## Prototype Status

Core backend workflow and FastAPI prototype API are implemented.

### Run the full prototype

The frontend is a Vite/React presentation layer over the canonical FastAPI backend. It no longer runs a separate Express API.

From the repository root in PowerShell, terminal 1:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
& ".\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api/*` to FastAPI.

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for the complete endpoint flow, demo sequence, live AI extraction path, and troubleshooting notes.

## Run the backend API

From the repository root:

```powershell
$env:PYTHONPATH="backend;."
python -m uvicorn app.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

See [docs/API_LAYER.md](./docs/API_LAYER.md) for the endpoint contract.

## Important

- Government verification is mocked for the prototype.
- AI does not make final compliance decisions.
- Compliance rules are deterministic.
- Officers remain the final decision-makers.
- Do not commit API keys, secrets, or real sensitive procurement documents.