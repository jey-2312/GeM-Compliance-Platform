# Saanron Development Progress — 2026-09-29

This checkpoint continues `SAANRON_6DAY_DEV_SPEC_UPDATED.md` from the post-tender-migration baseline.

## Completed in this checkpoint

### Deterministic rules
- Added `RULE-LOCAL-CONTENT-GTE` using the existing numeric-threshold evaluator pattern.
- Added `RULE-DEBARMENT-CLEAR` using the existing generalized status evaluator pattern.
- Added `RULE-CERTIFICATE-VALID-AT-CLOSING` as a deterministic temporal evaluator.
- Added materiality/counterfactual `gap_to_compliance` to numeric threshold failures.
- Added `critical` to compliance results; debarment failures are marked critical.

### Seed/demo data
- Tender A local-content scenario: 42% against 50% → FAIL with an 8 percentage-point gap.
- Tender A debarment registry: NOT_DEBARRED → PASS.
- Tender B local-content scenario: 55% against 40% → PASS.
- Tender B debarment registry: NOT_DEBARRED → PASS.
- Tender B certificate validity: 2026-12-15 against closing date 2026-11-12 → PASS.
- Added mock debarment registry data and corresponding evidence/verification fixtures.

### Deployment robustness
- Health endpoint now reports database, AI, and verification component state honestly for the in-memory prototype.
- Added `POST /api/v1/demo/reset`.
- Added document-hash extraction caching for successful live extraction.
- Live extraction now falls back to validated demo data instead of returning raw LLM failures.
- Added basic per-IP rate limiting to extraction and AI-costing endpoints.
- Corrected live extraction source paths to the actual `Tender_A.pdf` / `Tender_B.pdf` files.
- Added `GET /api/v1/demo/summary` for dataset-backed landing-page counts.

### Frontend
- Landing entry now exposes live seeded counts for tenders, requirements, evidence checks, contradictions, and manual-review items.
- Added `Start Guided Demo · 90 sec` entry point.
- Added guided-demo navigation through the existing overview, compliance, evidence-chain drawer, bidder passport, and activity views.
- Added visible materiality-gap and critical-result semantics to the compliance UI.

## Validation

- Backend + AI suite: **all tests passing**.
- Current suite includes tests for local content, debarment, temporal validity, materiality gaps, health/summary, live fallback, reset, and rate limiting.
- Frontend dependency installation was not available in the build container, so a full Vite production build was not independently executed in this checkpoint. Global TypeScript parsing/type analysis showed no additional semantic errors in the changed frontend files beyond unavailable project dependencies.

## Intentionally not claimed as complete

- React Flow Evidence Graph is not yet implemented.
- Dedicated Contradiction Radar aggregation UI is not yet implemented.
- Production hosting/keep-alive configuration is not performed from this repository checkpoint.
- Optional Class-I/Class-II local-content tiering is deferred.


## P1 continuation completed

### Evidence Graph
- Added `frontend/src/components/EvidenceGraphView.tsx`.
- The graph consumes the existing `GET /api/v1/evidence/{id}/chain` response instead of creating a competing provenance model.
- The view exposes eight trace stages: Tender Clause, Requirement, Extracted Claim, Evidence, Verification, Deterministic Rule, Compliance Result, and Audit/Action.
- Each node is selectable and opens a focused detail panel with source/value/provenance information.
- The graph intentionally uses native React/CSS in this checkpoint so no new frontend dependency is required; the backend contract remains compatible with a future React Flow rendering.

### Contradiction Radar
- Added `GET /api/v1/contradictions/{tender_id}/{bidder_id}`.
- Added the `ContradictionRadarResponse` API contract and frontend `ContradictionRadarView`.
- The endpoint aggregates the existing contradiction detector findings across the selected case.
- Severity is deterministic: `HIGH` when a finding is linked to a failed deterministic result; otherwise `MEDIUM`. This is an investigation signal and is explicitly not a fraud determination.
- Radar findings include source values, evidence IDs, result IDs, and links back to the existing evidence review flow.

### Guided demo and robustness polish
- Extended the guided demo from 6 to 7 stages so Evidence Graph and Contradiction Radar are visible before bidder passport and officer action.
- Added a `Reset Demo` control on the landing page using `POST /api/v1/demo/reset`.
- Added explicit extraction-confidence versus deterministic-compliance semantics to the case overview.
- Corrected the controlled tender intake response so it no longer claims live AI usage simply because an LLM key is configured; that path uses the frozen validated tender dataset after PDF recognition.
- Expanded manual verification request kinds to include the already-supported OEM and debarment providers.
- Cleaned duplicate schema/state declarations left by the previous feature checkpoint.

## Validation after P1 continuation

- Backend + AI tests: **75 passed**.
- Python `compileall` check: **passed**.
- Contradiction Radar API tests cover Tender A (`HIGH`) and Tender B (`MEDIUM`) behaviour.
- Frontend production build was **not** independently verified because `frontend/node_modules` is absent in the build container and `npm ci` could not complete within the container transport timeout. No new npm dependency was introduced by this checkpoint.

## Remaining P0/P1 items

- Production hosting / keep-alive configuration is deployment-environment dependent and has not been performed from the repository.
- The live Groq requirement extractor remains intentionally isolated behind the validated fallback; further adapter hardening can happen after the stable submission build.
- Optional Class-I/Class-II local-content tiering remains deferred.
- After the submission build is stable, adversarial testing should be performed against the deployed URL rather than localhost.
