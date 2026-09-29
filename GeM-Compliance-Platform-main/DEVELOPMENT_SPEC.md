# PS26100 — Prototype Development Specification
## Shared Team Implementation Guide — 18 September 2026 Prototype

> **Purpose:** This document is the shared implementation reference for everyone working in the repository.
>
> **Important:** This is the prototype development guide for the 18 September 2026 evaluation. It is not the complete production system specification.

---

# 1. Document Hierarchy

Everyone working on the repository should understand this hierarchy before writing code.all the documents are in project context folder

## 1. Prototype Development Specification — THIS DOCUMENT
**Authority:** Coding and integration

Use this document for:
- Prototype scope
- Architecture
- Shared data contracts
- APIs and interfaces
- Implementation boundaries
- Team responsibilities
- Testing
- Demo workflow

If another document conflicts with this document on prototype implementation, **this document wins**.

## 2. Product Reference
**Authority:** Full-product context

Use it to understand:
- Long-term product vision
- Full architecture
- Future modules
- Production security
- Advanced verification and graph capabilities

Do **not** use it to expand the 18 September prototype unnecessarily.

## 3. 18 Sep Internal Prototype & Team Plan
**Authority:** Deadline and execution context

Use it for:
- Team responsibilities
- Current evaluation priorities
- Build sequence
- Collaboration expectations

It does not override the technical contracts in this document.

## 4. Team Understanding
**Authority:** Conceptual / human context

Use it when someone needs a simple explanation of:
- The problem
- The product
- Bidder Evidence Passport
- AI vs code
- Evidence-driven verification

It is not the technical implementation authority.

## 5. Product Gist
**Authority:** Quick reference only

Useful for quickly remembering the product framing. It does not override the documents above.

### Conflict rule

```text
Prototype Development Specification
            ↓
Product Reference
            ↓
18 Sep Team Plan
            ↓
Team Understanding
            ↓
Product Gist
```

Higher-level documents must not be used to silently change lower-level prototype contracts.

---

# 2. Prototype Goal

Build one complete, evidence-backed bid compliance workflow that demonstrates:

```text
Tender PDF
    ↓
Requirement Extraction
    ↓
Structured TenderRequirement
    ↓
Bidder Evidence
    ↓
Verification
    ↓
Deterministic Rule Engine
    ↓
ComplianceResult
    ↓
Evidence / Explanation
    ↓
Officer Review
    ↓
AuditEvent
```

The prototype should prove the **core product concept**, not attempt to build the complete production platform.

---

# 3. Core Product Principle

Remember this throughout development:

> **AI understands. Code verifies. Evidence explains. The officer decides.**

Therefore:

### AI handles
- Tender language
- Requirement extraction
- Document understanding
- Semantic matching
- Entity resolution
- Contradiction identification
- Explanations

### Deterministic code handles
- Numeric comparisons
- Dates
- Expiry
- Percentages
- Required/optional conditions
- Source statuses
- PASS/FAIL logic
- Compliance calculations

The LLM must not be the final authority for arithmetic or deterministic compliance decisions.

---

# 4. Human Decision Authority

The system is a decision-support tool.

It must NOT:
- Automatically approve bidders
- Automatically reject bidders
- Declare fraud
- Confirm collusion

Instead:

```text
AI understands
      ↓
Code verifies
      ↓
Evidence explains
      ↓
Officer investigates
      ↓
Officer decides
```

---

# 5. Prototype Scope

## Must Demonstrate

1. Tender requirement extraction
2. Structured tender requirements
3. PyMuPDF PDF text extraction
4. OCR fallback if feasible
5. Bidder Evidence Passport
6. GST verification using mock data
7. PAN verification using mock data
8. Udyam verification using mock data
9. Turnover extraction
10. Turnover contradiction detection
11. Deterministic turnover rule
12. Evidence-backed compliance result
13. PASS / FAIL / MANUAL_REVIEW / PENDING / UNVERIFIABLE / NOT_APPLICABLE
14. Two tenders with different requirements
15. Audit/activity history
16. At least one real LLM integration

## Outside the Critical Path

Do not allow these to delay the core workflow:

- Production government API integrations
- Full authentication/RBAC/MFA
- PostgreSQL production deployment
- Advanced graph analytics
- Full-scale anomaly detection
- Sophisticated immutable audit infrastructure
- Training custom AI/OCR models
- Complete production security infrastructure

These belong to the full product or later stages.

---

# 6. Prototype Architecture

```text
                         ┌──────────────────────┐
                         │      Tender PDF      │
                         └──────────┬───────────┘
                                    ↓
                         ┌──────────────────────┐
                         │ PyMuPDF / OCR        │
                         └──────────┬───────────┘
                                    ↓
                         ┌──────────────────────┐
                         │ AI Requirement       │
                         │ Extraction           │
                         └──────────┬───────────┘
                                    ↓
                         ┌──────────────────────┐
                         │ TenderRequirement    │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
          ┌──────────────────┐             ┌──────────────────┐
          │ Bidder Evidence  │             │ RuleDefinition   │
          └────────┬─────────┘             └────────┬─────────┘
                   ↓                                ↓
          ┌──────────────────┐             ┌──────────────────┐
          │ Verification     │────────────→│ Rule Engine      │
          └──────────────────┘             └────────┬─────────┘
                                                    ↓
                                          ┌──────────────────┐
                                          │ ComplianceResult │
                                          └────────┬─────────┘
                                                   ↓
                                          ┌──────────────────┐
                                          │ Evidence Chain   │
                                          └────────┬─────────┘
                                                   ↓
                                          ┌──────────────────┐
                                          │ Frontend /       │
                                          │ Officer Review   │
                                          └────────┬─────────┘
                                                   ↓
                                          ┌──────────────────┐
                                          │ AuditEvent       │
                                          └──────────────────┘
```

---

# 7. Shared Domain Contract

These are the shared entities.

**Do not rename fields or create competing versions without team agreement.**

```text
Tender
TenderRequirement
Bidder
Document
ExtractedField
Evidence
Verification
ComplianceResult
AuditEvent
RuleDefinition
```

Pydantic/domain models should be the first backend implementation.

JSON/domain shapes should remain the contract between:
- Backend
- AI layer
- Frontend

---

# 8. Status Model

Use exactly:

```text
PASS
FAIL
MANUAL_REVIEW
PENDING
UNVERIFIABLE
NOT_APPLICABLE
```

Important distinction:

```text
UNVERIFIABLE ≠ FAIL
MANUAL_REVIEW ≠ FAIL
```

If the system cannot establish compliance, it should not automatically convert uncertainty into non-compliance.

---

# 9. Core Domain Shapes

## Tender

```json
{
  "id": "TND-001",
  "title": "Sample CPCL Procurement Tender",
  "reference_no": "CPCL/PROC/2026/001",
  "closing_date": "2026-09-30",
  "documents": ["DOC-TENDER-001"],
  "requirements": ["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
  "status": "READY"
}
```

## TenderRequirement

```json
{
  "id": "REQ-001",
  "tender_id": "TND-001",
  "type": "TURNOVER",
  "title": "Minimum Average Annual Turnover",
  "description": "Bidder must have average annual turnover of at least INR 5 crore.",
  "operator": "GREATER_THAN_OR_EQUAL",
  "threshold": 50000000,
  "unit": "INR",
  "mandatory": true,
  "source_document_id": "DOC-TENDER-001",
  "source_page": 7,
  "confidence": 0.96,
  "rule_id": "RULE-TURNOVER-GTE"
}
```

## Bidder

```json
{
  "id": "BIDDER-001",
  "legal_name": "ABC Technologies Pvt Ltd",
  "pan": "ABCDE1234F",
  "gstin": "29ABCDE1234F1Z5",
  "udyam": "UDYAM-KL-00-0000000",
  "address": "Sample Address",
  "evidence_ids": [
    "EVD-001",
    "EVD-002",
    "EVD-003",
    "EVD-004"
  ]
}
```

## Document

```json
{
  "id": "DOC-001",
  "bidder_id": "BIDDER-001",
  "name": "Audited_Financial_Statement.pdf",
  "document_type": "AUDITED_FINANCIALS",
  "path_or_uri": "data/bidders/abc/Audited_Financial_Statement.pdf",
  "page_count": 14,
  "text_extraction_method": "PYMUPDF",
  "ocr_used": false,
  "uploaded_at": "2026-09-17T09:00:00+05:30"
}
```

## ExtractedField

```json
{
  "id": "FIELD-001",
  "document_id": "DOC-001",
  "field_name": "average_annual_turnover",
  "value": 48000000,
  "unit": "INR",
  "normalized_value": 48000000,
  "raw_text": "Average annual turnover: Rs. 4.8 Crores",
  "page": 12,
  "confidence": 0.98,
  "extraction_method": "AI"
}
```

## Evidence

```json
{
  "id": "EVD-012",
  "bidder_id": "BIDDER-001",
  "requirement_id": "REQ-001",
  "document_id": "DOC-001",
  "page": 12,
  "evidence_type": "DOCUMENT_EXTRACT",
  "field_name": "average_annual_turnover",
  "value": 48000000,
  "unit": "INR",
  "source_label": "Audited Financial Statement",
  "confidence": 0.98,
  "verification_status": "VERIFIED",
  "notes": "Audited value conflicts with self-declared turnover."
}
```

## Verification

```json
{
  "id": "VER-001",
  "evidence_id": "EVD-012",
  "source_type": "MOCK_GOVERNMENT_SOURCE",
  "source_name": "Mock Financial Verification",
  "checked_at": "2026-09-17T09:10:00+05:30",
  "status": "VERIFIED",
  "verified_value": 48000000,
  "details": "Mock source confirms audited turnover value."
}
```

## ComplianceResult

```json
{
  "id": "CMP-001",
  "tender_id": "TND-001",
  "bidder_id": "BIDDER-001",
  "requirement_id": "REQ-001",
  "status": "FAIL",
  "rule_id": "RULE-TURNOVER-GTE",
  "expected": 50000000,
  "actual": 48000000,
  "evidence_ids": ["EVD-012", "EVD-013"],
  "finding_ids": ["FND-001"],
  "explanation": "Verified turnover of INR 4.8 crore is below the tender minimum of INR 5 crore.",
  "evaluated_at": "2026-09-17T09:12:00+05:30"
}
```

## AuditEvent

```json
{
  "id": "AUD-001",
  "timestamp": "2026-09-17T09:12:00+05:30",
  "actor_type": "SYSTEM",
  "action": "COMPLIANCE_EVALUATED",
  "tender_id": "TND-001",
  "bidder_id": "BIDDER-001",
  "requirement_id": "REQ-001",
  "rule_id": "RULE-TURNOVER-GTE",
  "result_id": "CMP-001",
  "details": "Rule evaluated against verified evidence."
}
```

## RuleDefinition

```json
{
  "id": "RULE-TURNOVER-GTE",
  "type": "NUMERIC_COMPARISON",
  "field": "average_annual_turnover",
  "operator": "GREATER_THAN_OR_EQUAL",
  "threshold_source": "requirement.threshold",
  "mandatory": true,
  "version": "1.0"
}
```

---

# 10. Contradictions Are Separate From Compliance

Do not collapse these concepts.

Example:

```text
Self-declared turnover: ₹6.2 Cr
Audited / verified turnover: ₹4.8 Cr
```

This creates:

```text
Contradiction finding
        ↓
MANUAL_REVIEW
```

Separately, if the tender requires:

```text
Turnover ≥ ₹5 Cr
```

then:

```text
₹4.8 Cr ≥ ₹5 Cr
FALSE
        ↓
ComplianceResult = FAIL
```

Therefore:

```text
Compliance Result
        +
Investigation Finding
```

are related but distinct concepts.

The system must not label the contradiction as fraud.

---

# 11. Bidder Evidence Passport

The Passport is a reusable evidence profile.

It can contain:

```text
Identity
├── Legal name
├── PAN
├── GSTIN
├── Udyam
└── Address

Statutory
├── GST status
├── PAN status
└── Udyam status

Financial
├── Turnover
├── Net worth
└── Relevant financial years

Experience
├── Projects
├── Clients
├── Dates
└── Values

Certifications
├── ISO
├── BIS
└── OEM

Verification History
└── Previous verification records
```

Important:

> The Passport stores evidence. The current tender determines compliance.

Do not create a permanent bidder “trust score” that replaces tender-specific evaluation.

---

# 12. Tender-Specific Compliance

The same bidder must be able to produce different results for different tenders.

Seed data:

```text
Bidder:
ABC Technologies Pvt Ltd

Verified turnover:
₹4.8 Cr

Tender A:
Minimum turnover = ₹5 Cr

Tender B:
Minimum turnover = ₹3 Cr
```

Expected:

```text
Tender A:
₹4.8 Cr >= ₹5 Cr
FALSE
→ FAIL

Tender B:
₹4.8 Cr >= ₹3 Cr
TRUE
→ PASS
```

This is a critical prototype demonstration.

---

# 13. Rule Engine

The Rule Engine receives structured requirements and verified bidder evidence.

It performs deterministic checks.

Example:

```text
TenderRequirement:
operator = GREATER_THAN_OR_EQUAL
threshold = 50000000

Verified evidence:
actual = 48000000

Rule:
48000000 >= 50000000

Result:
FALSE
```

The Rule Engine should handle:
- Numeric comparison
- Dates
- Expiry
- Percentages
- Status values
- Mandatory conditions
- Optional conditions

It should return a structured `ComplianceResult`.

Do not put LLM reasoning inside the final rule evaluator.

---

# 14. Evidence Chain

Every important result should be traceable.

The conceptual chain is:

```text
Tender Clause
     ↓
Requirement
     ↓
Rule
     ↓
Required Evidence
     ↓
Bidder Claim
     ↓
Evidence Document / Page
     ↓
Extracted Value
     ↓
External Verification
     ↓
Cross-Check
     ↓
Compliance Result
     ↓
Officer Action
```

An officer should be able to answer:

> “Why did the system produce this result?”

without trusting an unexplained AI statement.

---

# 15. Document Processing

Prototype pipeline:

```text
PDF
 ↓
PyMuPDF text extraction
 ↓
Is useful text available?
 ├── YES → continue
 └── NO / insufficient → OCR fallback
                         ↓
                      PaddleOCR
                         ↓
                  page-aware text
                         ↓
                 AI extraction
```

OCR is a fallback, not a separate compliance system.

Do not train an OCR model for this prototype.

If OCR becomes time-consuming, the core prototype should continue using digital PDFs.

---

# 16. Mock Government Connectors

Prototype integrations should use a replaceable connector pattern.

Example:

```text
GSTConnector
PANConnector
UdyamConnector
FinancialVerificationConnector
```

Prototype:

```text
Connector interface
       ↓
Mock implementation
       ↓
Structured Verification
```

Production:

```text
Connector interface
       ↓
Authorized government integration
       ↓
Structured Verification
```

Never present mock verification as a real government API result.

---

# 17. Frontend Contract

The frontend should consume the shared domain objects rather than inventing a second data model.

Core screens:

### 1. Tender Dashboard
- Tender information
- Requirement summary
- Compliance overview

### 2. Requirement View
- Requirement
- Threshold
- Mandatory/optional
- Source page
- Confidence

### 3. Bidder Passport
- Identity
- GST/PAN/Udyam
- Financial evidence
- Verification status

### 4. Compliance Matrix
- Requirement
- Result
- Evidence
- Finding
- Explanation

### 5. Evidence Drill-Down
Show:

```text
Requirement
Result
Expected value
Actual value
Evidence
Document
Page
Verification
Rule
Confidence
Explanation
Officer action
```

### 6. Audit / Activity History
Show important events chronologically.

---

# 18. Suggested API Contract

```text
POST /api/tenders
POST /api/tenders/{id}/extract
GET  /api/tenders/{id}

POST /api/bidders
POST /api/documents

POST /api/bidders/{id}/verify

POST /api/compliance/check
GET  /api/compliance/{tender_id}/{bidder_id}

GET /api/evidence/{id}
GET /api/bidders/{id}/passport
GET /api/audit/{tender_id}/{bidder_id}
```

The exact API implementation can evolve, but the underlying domain objects must remain consistent.

---

# 19. Repository Structure

A practical structure is:

```text
project-root/
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── rules/
│   │   ├── evidence/
│   │   ├── verification/
│   │   └── services/
│   │
│   └── tests/
│
├── ai/
│   ├── prompts/
│   ├── extraction/
│   └── schemas/
│
├── data/
│   ├── tenders/
│   ├── bidders/
│   ├── mock_sources/
│   └── fixtures/
│
├── docs/
│   └── schemas/
│
└── README.md
```

Teams may adapt folder names where necessary, but shared contracts should not drift.

---

# 20. Team Responsibilities

## Frontend Developer

Own:
- Dashboard
- Requirement views
- Bidder Passport UI
- Compliance matrix
- Evidence drill-down
- Audit/activity UI
- API integration

Must understand:
- Domain schemas
- Statuses
- Evidence chain
- ComplianceResult

Should not invent frontend-only meanings for backend statuses.

---

## AI / Document Intelligence Developer

Own:
- PDF text extraction integration
- OCR fallback
- Document understanding
- Tender requirement extraction
- Structured AI output
- Field extraction
- Contradiction detection
- Confidence values

Must output the agreed domain structures.

AI should propose/interpret information.

It should not independently decide deterministic compliance.

---

## Backend / Rule / Evidence Developer

Own:
- Shared Pydantic/domain schemas
- Seed fixtures
- Rule Engine
- Evidence Engine
- Verification layer
- Compliance evaluation
- Audit events
- Backend integration

Must keep the shared contract stable.

---

# 21. Working Together Without Schema Drift

Before changing a shared object:

```text
1. Check this specification.
2. Check whether another workstream already consumes the field.
3. Prefer the existing field name.
4. If a change is genuinely necessary, communicate it to the team.
5. Update the shared contract before changing dependent code.
```

Avoid:

```text
Backend:
average_annual_turnover

AI:
annual_turnover

Frontend:
turnoverValue
```

when all three represent the same domain field.

Use one agreed representation.

---

# 22. Git / Collaboration Rules

Recommended workflow:

```text
main
 │
 ├── frontend/*
 ├── ai/*
 ├── backend/*
 └── integration/*
```

Rules:

- Keep commits small and meaningful.
- Do not commit secrets/API keys.
- Do not modify another workstream's code casually.
- Pull/rebase before major integration work.
- Run tests before merging.
- Do not silently change shared schemas.
- Use fixtures for predictable integration testing.
- Keep mock data clearly labelled as mock.

Suggested commit style:

```text
feat: add turnover rule evaluator
feat: add tender requirement extraction
feat: add bidder passport endpoint
fix: handle missing extracted turnover
test: add tender-specific compliance cases
```

---

# 23. Environment and Secrets

Never commit:

```text
.env
API keys
LLM keys
Government credentials
Passwords
Private certificates
Real procurement documents containing sensitive information
```

Commit a safe example instead:

```text
.env.example
```

Example:

```text
LLM_API_KEY=
LLM_MODEL=
BACKEND_URL=
```

---

# 24. Testing Strategy

The first tests should prove deterministic behavior.

## Test 1 — Tender A

```text
actual = ₹4.8 Cr
threshold = ₹5 Cr

expected:
FAIL
```

## Test 2 — Tender B

```text
actual = ₹4.8 Cr
threshold = ₹3 Cr

expected:
PASS
```

## Test 3 — Missing evidence

```text
actual = unavailable

expected:
UNVERIFIABLE
```

## Test 4 — Unclear AI interpretation

```text
confidence below chosen threshold

expected:
MANUAL_REVIEW
```

## Test 5 — Contradiction

```text
declared = ₹6.2 Cr
audited = ₹4.8 Cr

expected:
investigation finding
not automatic fraud
```

---

# 25. Seed Data

Use one bidder:

```text
ABC Technologies Pvt Ltd
```

Identity:

```text
PAN:
ABCDE1234F

GSTIN:
29ABCDE1234F1Z5

Udyam:
UDYAM-KL-00-0000000
```

Verification:

```text
GST:
ACTIVE

PAN:
VALID

Udyam:
ACTIVE
```

Financial evidence:

```text
Self-declared turnover:
₹6.2 Cr

Audited / verified turnover:
₹4.8 Cr
```

Tenders:

```text
Tender A:
Minimum turnover = ₹5 Cr

Tender B:
Minimum turnover = ₹3 Cr
```

---

# 26. First Implementation Slice

Do not start by building the entire platform.

Start here:

```text
Shared Pydantic schemas
        ↓
Seed fixtures
        ↓
RULE-TURNOVER-GTE
        ↓
Deterministic evaluator
        ↓
ComplianceResult
        ↓
Tests
```

Only after this is stable should the team integrate:
- AI extraction
- document processing
- verification
- APIs
- frontend

---

# 27. Recommended Integration Sequence

```text
PHASE 1
Shared contracts
+
Seed data
+
Rule Engine
+
Tests

        ↓

PHASE 2
Document processing
+
AI extraction
+
Evidence generation

        ↓

PHASE 3
Verification
+
Contradiction detection

        ↓

PHASE 4
API integration

        ↓

PHASE 5
Frontend

        ↓

PHASE 6
End-to-end demo

        ↓

PHASE 7
Polish / bug fixing
```

Do not wait until the end to discover that the frontend and backend disagree on the data model.

---

# 28. Demo Workflow

The final prototype should tell one simple story.

```text
1. Open Tender A
       ↓
2. AI extracts:
   Turnover ≥ ₹5 Cr
       ↓
3. Open ABC Technologies Passport
       ↓
4. Show declared turnover:
   ₹6.2 Cr
       ↓
5. Show audited / verified turnover:
   ₹4.8 Cr
       ↓
6. Show contradiction
       ↓
7. Rule Engine checks:
   ₹4.8 Cr ≥ ₹5 Cr
       ↓
8. FAIL
       ↓
9. Open Evidence
       ↓
10. Show document + page + value + verification + rule
        ↓
11. Open Tender B
        ↓
12. Requirement:
    Turnover ≥ ₹3 Cr
        ↓
13. Same bidder
        ↓
14. PASS
        ↓
15. Show audit history
        ↓
16. Officer reviews the evidence
```

The key message is:

> **The bidder did not change. The tender requirement changed. Therefore the compliance result changed.**

---

# 29. Definition of Done

The prototype foundation is complete when:

- Shared domain schemas exist.
- Seed fixtures load successfully.
- Tender A and Tender B exist.
- Bidder Passport data exists.
- GST/PAN/Udyam mock verification exists.
- Turnover evidence exists.
- Contradiction can be represented separately.
- `RULE-TURNOVER-GTE` works deterministically.
- Tender A returns `FAIL`.
- Tender B returns `PASS`.
- Evidence is attached to the result.
- ComplianceResult contains an explanation.
- AuditEvent is generated.
- Tests pass.
- No secrets are committed.
- The frontend and AI layers can consume the shared structures without creating parallel schemas.

---

# 30. What Not To Do

Do not:

- Build unrelated features because they sound impressive.
- Train a custom LLM.
- Build production government integrations for the prototype.
- Let an LLM perform final arithmetic.
- Treat missing verification as automatic FAIL.
- Treat contradiction as automatic fraud.
- Automatically approve/reject bidders.
- Hard-code the final product name.
- Create a permanent bidder trust score.
- Build sophisticated blockchain infrastructure merely because the SIH theme mentions blockchain/cybersecurity.
- Over-engineer the database before the core workflow works.
- Build the entire UI before the backend contract is stable.

---

# 31. Product Name

The final product name is **not decided yet**.

Use:

```text
PROJECT_NAME
```

or a configurable environment/config value.

Do not hard-code `BidTrace` as the final product name throughout the implementation.

---

# 32. Prototype vs Full Product

The prototype is deliberately smaller than the eventual platform.

```text
18 SEP PROTOTYPE
        ↓
Proof of core workflow
        ↓
Selection / next round
        ↓
FULL PRODUCT
```

The full product may later include:
- Authorized government connectors
- PostgreSQL / pgvector
- Advanced relationship graphs
- More document types
- Production authentication/RBAC/MFA
- Stronger audit infrastructure
- Advanced anomaly analysis
- More sophisticated security controls
- Larger-scale document processing

Do not confuse future architecture with current prototype requirements.

---

# 33. Shared Mental Model

Every team member should be able to explain these five questions:

### 1. What does the tender require?
**Tender Intelligence**

### 2. What does the bidder claim?
**Bidder Evidence Passport**

### 3. What evidence supports the claim?
**Evidence + Verification**

### 4. Does the bidder satisfy this specific tender?
**Deterministic Compliance Engine**

### 5. What should the officer do?
**Evidence Investigation + Human Decision**

---

# 34. Final Team Principle

The repository should be built around this chain:

```text
REQUIREMENT
     ↓
EVIDENCE
     ↓
VERIFICATION
     ↓
RULE
     ↓
COMPLIANCE RESULT
     ↓
EXPLANATION
     ↓
OFFICER ACTION
     ↓
AUDIT
```

If a feature cannot clearly connect to this workflow, question whether it belongs in the prototype.

> **Build the smallest complete evidence-backed workflow first.**
>
> **Do not build disconnected impressive features.**
