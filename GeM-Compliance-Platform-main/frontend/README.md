# GeM Compliance Platform - Frontend

The frontend is a Vite + React + TypeScript officer interface for the prototype.

## Current interaction model

The frontend no longer preloads a tender selector. A reviewer starts a new case by uploading a tender PDF.

```text
Tender PDF
   -> FastAPI intake
   -> page-aware extraction
   -> structured tender requirements
   -> deterministic compliance evaluation
   -> officer dossier
```

For the controlled prototype, use the supplied synthetic documents:

- `../data/tenders/Tender_A.pdf`
- `../data/tenders/Tender_B.pdf`

Tender A should be opened first. Tender B is then opened through the same `New review` flow. The bidder passport keeps the reusable bidder evidence and adds the tender-specific evaluations only after those tenders have actually been reviewed in the current session.

## Run

```bash
npm install
npm run dev
```

Set `VITE_API_BASE_URL` only when the FastAPI base path is not the default `/api/v1`.

The visible project name can be configured with `VITE_PROJECT_NAME`.
