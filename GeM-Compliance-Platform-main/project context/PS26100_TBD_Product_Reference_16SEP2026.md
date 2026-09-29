# PS 26100 — TBD Product Reference Document

## AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

**SIH 2026 Problem Statement:** PS 26100  
**Organization:** Ministry of Petroleum & Natural Gas / CPCL  
**Product Name:** **TBD**  
**Purpose:** Source of truth for the actual product and long-term solution

---

# 1. What We Are Building

TBD is an AI-powered platform that helps procurement officers verify whether a bidder satisfies the **specific requirements of a specific tender**.

GeM may verify a seller during registration, but bid-time verification still depends on tender-specific requirements, submitted evidence, current source information, dates, thresholds and other conditions.

TBD connects these pieces into one workflow.

> **GeM verifies at registration. We verify at bid-time, against the specific requirements of the specific tender.**

The platform reads the tender, identifies its requirements, builds a verified bidder evidence profile, cross-checks the information, applies deterministic compliance rules, highlights contradictions and risks, and gives the officer an explainable view of the evidence.

The platform is a **decision-support system**. The procurement officer remains responsible for the final decision.

---

# 2. The Core Problem

A procurement officer may need to verify information spread across:

- Tender documents
- Bidder declarations
- Financial statements
- GST / PAN / Udyam information
- MCA/company information
- EPFO / ESIC information where applicable
- OEM authorization
- Local-content or Make in India claims
- Experience and completion certificates
- Debarment / blacklist information
- Other tender-specific evidence

The difficult part is not simply finding the documents.

The difficult part is connecting:

> **What the tender requires → what the bidder claims → what the evidence says → what external sources say → what the rule means for this tender.**

TBD is designed to automate this connection while keeping the officer in control.

---

# 3. The Product in One Flow

```text
Tender PDF
   ↓
Tender Intelligence
   ↓
Requirements + Conditions
   ↓
Tender-Specific Rulebook
   ↓
Bidder Documents + Source Data
   ↓
Document Intelligence
   ↓
Unified Bidder Evidence Passport
   ↓
Cross-Document + Cross-Source Verification
   ↓
Contradiction / Anomaly Analysis
   ↓
Compliance Engine
   ↓
Evidence + Explanation + Risk
   ↓
Officer Investigation Desk
   ↓
Officer Decision
```

---

# 4. Product Principles

## Tender-aware

Compliance is not a permanent label attached to a company.

The same bidder may satisfy one tender and fail another because the requirements are different.

```text
                    BIDDER
                       │
              ┌────────┴────────┐
              ↓                 ↓
          TENDER A           TENDER B
              ↓                 ↓
          Requirements       Requirements
              ↓                 ↓
             PASS             REVIEW/FAIL
```

## Evidence-first

The system should never make an important finding without being able to show the evidence behind it.

> **Requirement → Evidence → Verification → Rule → Result → Reason**

## AI-assisted, not AI-decided

AI is used for understanding and interpretation.

Deterministic code is used for exact compliance logic.

The officer makes the final decision.

---

# 5. Core Product Modules

## 5.1 Tender Intelligence

The system reads the tender and identifies:

- Eligibility requirements
- Mandatory / optional conditions
- Financial thresholds
- Experience requirements
- Technical requirements
- Certificates and authorizations
- Local-content requirements
- Date and validity conditions
- Required evidence
- Other tender-specific conditions

The output becomes a structured **Tender Rulebook**.

---

## 5.2 Document Intelligence

Bidder documents may be PDFs, scanned documents or other supported formats.

The document engine performs:

- Document classification
- Text extraction
- OCR for scanned documents
- Field extraction
- Date extraction
- Name and identifier extraction
- Table / financial information extraction
- Evidence location and page tracking

The goal is to turn unstructured documents into usable evidence.

---

## 5.3 Bidder Evidence Passport

The Bidder Passport is a reusable evidence profile for a bidder.

It can contain:

### Identity
- Legal name
- PAN
- GSTIN
- CIN
- Udyam
- Registered address
- Directors / signatories
- Other identity links

### Financial
- Turnover
- Net worth
- Profitability
- Relevant financial years
- Financial statements

### Experience
- Similar projects
- Client information
- Project value
- Dates
- Completion status
- Relevant certificates

### Certifications and Authorization
- OEM authorization
- ISO / BIS and other relevant certifications
- Validity dates
- Scope of authorization

### Statutory / Regulatory
- GST
- Udyam
- PAN
- MCA
- EPFO / ESIC where relevant
- Debarment / blacklist status
- Other applicable verification sources

### Historical Evidence
- Previous verification results
- Past issues
- Previous clarifications
- Repeated inconsistencies
- Evidence history

The passport stores evidence about the bidder, but **current tender requirements still determine current compliance**.

---

# 6. Cross-Verification

TBD compares information in three directions:

### Document ↔ Document

Example:

```text
Self Declaration:     ₹6.2 Cr
Audited Statement:    ₹4.8 Cr

→ Financial contradiction
```

### Document ↔ Source

Example:

```text
Bidder GST Certificate
        ↕
Verified GST source

→ Status matches / mismatch
```

### Identity ↔ Identity

Example:

```text
PAN
GSTIN
CIN
Udyam
Company Name
Address
Directors / Signatories

→ Same entity / possible mismatch
```

This creates a more reliable evidence picture.

---

# 7. Contradiction Radar

Contradiction Radar identifies information that does not agree across evidence sources.

Possible examples:

### Financial

```text
Self Declaration       ₹6.2 Cr
Audited Statement      ₹4.8 Cr
Verified Source        ₹4.8 Cr

⚠ FINANCIAL CONTRADICTION
```

### Identity

```text
PAN:  ABC Technologies Pvt Ltd
GST:  ABC Technology Private Limited

⚠ NAME MISMATCH
```

### Date

```text
Certificate: Valid until 2025
Tender closing date: 2026

⚠ POSSIBLE EXPIRY ISSUE
```

### Technical

```text
Tender requirement: RAM ≥ 16 GB
Datasheet:          16 GB
Declaration:         8 GB

⚠ SPECIFICATION CONFLICT
```

The system should flag these as **issues requiring investigation**.

It should not automatically label them as fraud.

---

# 8. Requirement Lineage and Evidence Investigation

Every important compliance result should have a traceable chain:

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
Evidence Document
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

The officer should be able to move from a result back to the source evidence.

Example:

```text
REQUIREMENT
Average annual turnover ≥ ₹5 Cr

BIDDER CLAIM
₹6.2 Cr

SOURCE
Self Declaration.pdf — Page 2

CONTRADICTING EVIDENCE
₹4.8 Cr

SOURCE
Audited Financials.pdf — Page 7

VERIFICATION
₹4.8 Cr

RULE
average_turnover >= ₹5 Cr

RESULT
FAIL / MANUAL REVIEW

REASON
Declared turnover conflicts with verified financial evidence.
```

This is one of the defining experiences of TBD.

---

# 9. Compliance Engine

The compliance engine applies the tender-specific rules to the verified evidence.

It should use explicit statuses such as:

- **PASS**
- **FAIL**
- **PENDING**
- **NOT APPLICABLE**
- **UNVERIFIABLE**
- **MANUAL REVIEW**

The system should not hide critical failures inside a single average score.

A dashboard can show:

```text
20 Requirements
18 PASS
1 FAIL
1 MANUAL REVIEW
0 PENDING

Overall:
REQUIRES OFFICER REVIEW
```

A numerical compliance score can still exist as a secondary indicator if required by the procurement workflow.

---

# 10. AI and Deterministic Logic

## AI should handle

- Tender language interpretation
- Requirement extraction
- Document understanding
- Semantic matching
- Entity resolution
- Contradiction identification
- Plain-language explanation
- Other unstructured-text interpretation

## Deterministic software should handle

- Numeric thresholds
- Dates
- Expiry
- Percentages
- Required / optional conditions
- Source status checks
- PASS / FAIL conditions
- Compliance calculations
- Rule versions

Example:

```text
Tender:
Minimum turnover = ₹5 Cr
       ↓
AI extracts requirement
       ↓
Structured rule
       ↓
Rule Engine
       ↓
Verified turnover = ₹4.8 Cr
       ↓
₹4.8 Cr < ₹5 Cr
       ↓
FAIL
```

The LLM should not be responsible for simple arithmetic or critical logical decisions.

---

# 11. AI Uncertainty and Explainability

Confidence should describe **AI interpretation**, not pretend to describe legal or procurement certainty.

Good:

```text
AI extraction confidence: 92%
```

or:

```text
AI interpretation:
Medium confidence

→ Manual review recommended
```

For deterministic rules, show the actual evidence and rule result instead.

```text
Extracted value: ₹4.8 Cr
Requirement: ≥ ₹5 Cr
Rule result: FALSE
Status: FAIL
```

Every important AI-assisted finding should include a reason and its supporting evidence.

---

# 12. Verification Provenance

Every important verification should maintain provenance.

Example:

```text
Verification ID: GST-10291
Source: GST Verification
Source Type: Government Source / Mock Source
Input Identifier: GSTIN XXXXX
Timestamp: [verification time]
Response: ACTIVE
Evidence: GST_Certificate.pdf
Rule Version: GST_ACTIVE_001
Result: VERIFIED
```

In the full product, stronger integrity and audit controls can be added around this record.

---

# 13. Government Source Integration

The architecture should use replaceable connectors.

```python
gst_connector.verify(gstin)
udyam_connector.verify(udyam_number)
mca_connector.verify(cin)
```

The product should support a connector pattern so a prototype or development connector can later be replaced with an **authorized production integration**.

Potential source categories include:

- PAN / Income Tax
- GST
- Udyam / MSME
- MCA
- EPFO
- ESIC
- Debarment / blacklist sources
- Other approved procurement-related sources

The product should never claim live government access unless the integration is actually authorized and operational.

---

# 14. Officer Investigation Desk

The officer should have an action-oriented workspace.

```text
OFFICER INVESTIGATION DESK

Critical Issues
Manual Reviews
Verified Requirements
Pending Items

NEEDS ATTENTION

Bidder: ABC Technologies
Issue: Turnover contradiction

[Review Evidence]

Bidder: XYZ Systems
Issue: Experience certificate unclear

[Review Evidence]
```

Opening an issue should show:

```text
Requirement
Evidence
Source
Verification
Rule
Result
Reason
Suggested Next Action
Officer Decision
```

The system assists investigation; it does not replace it.

---

# 15. Clarification Workflow

When evidence is missing, ambiguous or inconsistent, the system can support a clarification workflow.

The platform can:

1. Identify the missing or unclear evidence.
2. Explain why clarification is required.
3. Draft a clarification request.
4. Record the clarification status.
5. Attach the response to the case.
6. Re-run the relevant verification.
7. Update the evidence trail and audit record.

The officer remains responsible for sending, accepting and acting on the clarification.

---

# 16. Multi-Bidder View

The platform should allow an officer to compare bidders across the same tender.

Example:

```text
                     Bidder A  Bidder B  Bidder C

GST                    PASS      PASS      PASS
PAN                    PASS      PASS      PASS
Turnover               PASS      FAIL      PASS
OEM                     PASS      REVIEW    PASS
Experience              PASS      PASS      FAIL
Local Content           REVIEW    PASS      PASS
```

This lets the officer see where the major differences are without opening every document separately.

---

# 17. Bidder Relationship and Anomaly Analysis

TBD can identify potential relationships or unusual patterns between bidders.

Possible signals:

- Shared address
- Shared directors
- Shared signatories
- Shared contact information
- Other relevant shared identifiers
- Unusual pricing similarities
- Other defined anomaly signals

This should be presented as:

> **Bidder Relationship & Anomaly Analysis**

Not as automatic proof of collusion.

Example:

```text
Bidder A ── shared address ── Bidder B
Bidder B ── shared signatory ─ Bidder C
Bidder A ── pricing similarity ─ Bidder C

→ Potential relationship / anomaly
→ Officer investigation recommended
```

---

# 18. Relationship and Evidence Graphs

The platform can provide visual graphs for two different purposes.

## Bidder Relationship Graph

Shows relationships between bidders and shared attributes.

## Compliance Evidence Graph

Shows the lineage of one finding:

```text
Tender Clause
      ↓
Requirement
      ↓
Bidder Claim
      ↓
Evidence
      ↓
Verification
      ↓
Rule
      ↓
Result
      ↓
Officer Action
```

The graphs are intended to make complex relationships understandable and auditable.

---

# 19. Security Architecture

Because TBD handles sensitive procurement information, security is part of the product design.

The full solution should include:

- Secure authentication
- Role-based access control
- Multi-factor authentication
- Protected API routes
- Server-side authorization
- Password hashing
- File validation
- Malware scanning
- Secure document storage
- Audit logging
- Encryption in transit and at rest
- Secrets management
- Security monitoring
- Backup and recovery controls
- Formal security testing

The production implementation should follow applicable government security requirements and approved infrastructure.

---

# 20. LLM and Document Security

Bidder documents are untrusted input.

The platform should treat:

> **Text inside a document as evidence to analyze, not as instructions to execute.**

The AI layer should be constrained to permitted tasks such as:

- Extraction
- Interpretation
- Analysis
- Explanation

It should not execute arbitrary instructions contained in uploaded documents.

---

# 21. Roles and Access

The full product can use role-based access such as:

### Procurement Officer
- Review tenders
- Review bidders
- Inspect evidence
- Request clarification
- Record final decisions

### Procurement Administrator
- Manage users
- Manage roles
- Manage system configuration

### Auditor
- Read audit history
- Inspect verification provenance
- Review decision trails

### System / Integration Services
- Perform approved source verifications
- Record verification events
- Operate connector workflows

Exact role names can be refined during implementation.

---

# 22. Audit Trail

Important actions should be recorded, including:

- Tender creation
- Document upload
- Extraction event
- Verification event
- Rule version used
- Compliance result
- Evidence review
- Clarification
- Officer action
- Final decision
- Administrative changes

The audit trail should help answer:

> **Who did what, when, using which evidence and which rule version?**

---

# 23. Product Data Model

Core entities:

```text
User
Role
Tender
TenderRequirement
ComplianceRule

Bid
Bidder
BidderEvidencePassport
Document
ExtractedField
Evidence

Verification
VerificationSource
ComplianceResult
Finding
RiskFlag

Clarification
OfficerAction
OfficerDecision
BidderRelationship

AuditEvent
```

The exact database schema can evolve during development.

---

# 24. Technology Architecture

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- Python
- FastAPI

## Document Processing

- PyMuPDF
- OCR such as PaddleOCR
- Document classification / parsing

## AI

- LLM with structured JSON output
- Embeddings / semantic matching where needed

## Database

- PostgreSQL
- pgvector where semantic retrieval is required

## Graph Analysis

- NetworkX
- React Flow or Cytoscape.js

## Authentication

- JWT or approved identity infrastructure
- RBAC
- MFA

## Deployment

- Docker
- Production deployment infrastructure appropriate to the target environment

---

# 25. Long-Term Product Architecture

```text
                         TENDER
                           │
                           ▼
                 TENDER INTELLIGENCE
                           │
                           ▼
              REQUIREMENTS + RULEBOOK
                           │
                           ▼
                  ┌────────────────┐
                  │ BIDDER EVIDENCE│
                  └───────┬────────┘
                          │
                  ┌───────┴────────┐
                  ▼                ▼
             DOCUMENTS         SOURCES
                  │                │
                  └───────┬────────┘
                          ▼
              BIDDER EVIDENCE PASSPORT
                          │
                          ▼
             CROSS-VERIFICATION LAYER
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
      CONTRADICTION RADAR      RELATIONSHIP ANALYSIS
              │                       │
              └───────────┬───────────┘
                          ▼
                COMPLIANCE ENGINE
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
            PASS       REVIEW        FAIL
              │           │           │
              └───────────┼───────────┘
                          ▼
             EVIDENCE + EXPLANATION
                          │
                          ▼
              OFFICER INVESTIGATION DESK
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       CLARIFICATION              OFFICER ACTION
              │                       │
              └───────────┬───────────┘
                          ▼
                    FINAL DECISION
                          │
                          ▼
                     AUDIT TRAIL
```

---

# 26. What Makes TBD Different

The market already contains systems with combinations of:

- Tender extraction
- Bidder extraction
- Government-source verification
- Deterministic compliance rules
- Evidence linking
- Audit trails
- Human review
- Anti-collusion analysis

Therefore, we should not claim that any one of these capabilities is completely unique.

Our product direction is to make the **investigation experience** and **reusable bidder evidence** central.

## Our strongest product ideas

### Bidder Passport

Evidence about a bidder can be reused across tenders.

### Tender-Dependent Compliance

The same bidder can receive different compliance outcomes for different tenders because the requirements differ.

### Evidence Investigation

The officer can move from:

> Requirement → Claim → Evidence → Source → Verification → Rule → Result → Action

### Contradiction Radar

The system actively highlights conflicts across evidence rather than only generating a score.

### Officer-Centered Workflow

The end product is designed around what the officer needs to investigate and decide.

---

# 27. Example End-to-End Scenario

Tender:

```text
Average turnover ≥ ₹5 Cr
Valid GST
Valid PAN
Valid Udyam
OEM authorization required
Minimum relevant experience
No current debarment
```

Bidder submits:

```text
Self Declaration
Audited Financial Statements
GST Certificate
PAN
Udyam Certificate
OEM Authorization
Experience Certificates
```

TBD:

```text
1. Reads tender
2. Extracts requirements
3. Creates rulebook
4. Builds bidder evidence passport
5. Verifies identifiers and status
6. Finds turnover contradiction
7. Checks turnover against tender rule
8. Flags the requirement for review
9. Shows all supporting evidence
10. Adds the issue to the Officer Investigation Desk
```

Officer:

```text
Reviews evidence
Requests clarification if needed
Records decision
```

---

# 28. Product Philosophy

The strongest description of TBD is:

> **AI understands.  
> Code verifies.  
> Evidence explains.  
> The officer decides.**

And the central product idea is:

> **From compliance score to compliance evidence and investigation.**

---

# 29. Boundaries and Honest Claims

We should not claim:

- AI detects fraud with certainty
- AI confirms collusion
- AI automatically rejects bidders
- AI makes final procurement decisions
- Live government APIs are already integrated unless they actually are
- Evidence verification itself is completely novel

We should claim:

- AI-assisted interpretation
- Deterministic compliance checking
- Cross-document and source verification
- Evidence-backed results
- Reusable bidder evidence
- Explainable officer workflows
- Potential anomaly / relationship analysis
- Architecture designed for authorized production integrations

---

# 30. Product Evolution

The product evolves in stages.

## Stage 1 — Demonstration

A small end-to-end proof that the core concept works.

## Stage 2 — Full Prototype

A broader working platform covering the major product modules described in this document.

## Stage 3 — Production-Oriented System

Authorized government integrations, stronger security, scale, reliability, audit controls, operational monitoring and deployment in an approved environment.

The details of the Stage 1 demonstration are maintained in a **separate 18 September Prototype Plan** and should not be treated as the definition of the actual product.

---

# 31. Final Product Definition

TBD is:

> **An evidence-driven tender compliance and investigation platform that connects tender requirements, bidder claims, submitted documents, verified source information, contradictions, deterministic rules and officer actions into one traceable workflow.**

The core journey is:

```text
TENDER
   ↓
REQUIREMENT
   ↓
BIDDER EVIDENCE
   ↓
VERIFICATION
   ↓
CROSS-CHECK
   ↓
CONTRADICTION / ANOMALY
   ↓
RULE
   ↓
RESULT
   ↓
INVESTIGATION
   ↓
OFFICER DECISION
   ↓
AUDIT TRAIL
```

This document describes the **actual TBD product vision and long-term solution**, not the limited 18 September internal prototype.
