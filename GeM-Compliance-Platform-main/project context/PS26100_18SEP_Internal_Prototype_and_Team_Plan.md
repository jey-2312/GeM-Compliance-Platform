# PS 26100 — 18 September Prototype & Team Execution Plan

## BidTrace — Internal Evaluation Build

**Date:** 18 September 2026  
**Purpose:** Build and demonstrate a small, reliable proof-of-concept for the internal SIH evaluation.

> This document is ONLY about the 18 September build.  
> It is not the definition of the full BidTrace product.

---

# 1. Our Goal for 18 September

We are not trying to build the full platform.

We are proving one thing:

> **Can we show a complete tender → bidder evidence → verification → compliance → evidence review workflow that actually works?**

The prototype should be small, stable and easy to explain.

A polished working flow is more useful than ten half-working features.

---

# 2. What We Must Demonstrate

The 18 September prototype should contain these core pieces:

1. **Tender upload / sample tender**
2. **Requirement extraction**
3. **Bidder document / data input**
4. **Structured bidder information**
5. **Mock source verification**
6. **Deterministic compliance checks**
7. **Evidence drill-down**
8. **Simple compliance dashboard**
9. **Bidder Passport demonstration**
10. **One strong contradiction example**

Everything else is secondary.

---

# 3. Exact Demo Scenario

Use one realistic synthetic tender.

Example requirements:

```text
Turnover ≥ ₹5 Cr
Valid GST
Valid PAN
Valid Udyam
OEM authorization required
```

Use one main synthetic bidder.

Create an intentional contradiction:

```text
Self Declaration:
₹6.2 Cr

Audited Statement:
₹4.8 Cr

Tender:
Requires ≥ ₹5 Cr
```

The system should detect:

```text
⚠ Financial contradiction

Requirement:
Turnover ≥ ₹5 Cr

Verified value:
₹4.8 Cr

Result:
FAIL

Action:
MANUAL REVIEW REQUIRED
```

The officer can open the issue and see the supporting evidence.

---

# 4. The Bidder Passport Demo

This is our visual differentiator for the demo.

Use the same bidder with two sample tenders.

```text
ABC Technologies
Verified turnover: ₹4.8 Cr
```

Tender A:

```text
Requirement:
Turnover ≥ ₹5 Cr

Result:
FAIL
```

Tender B:

```text
Requirement:
Turnover ≥ ₹3 Cr

Result:
PASS
```

The point is simple:

> **Compliance depends on the bidder AND the tender requirements.**

The passport stores reusable evidence; the current tender determines the current result.

---

# 5. 18 September Feature Priority

## MUST WORK

### 1. Requirement extraction

A sample tender goes in and produces structured requirements.

### 2. Bidder information

A synthetic bidder dataset / documents produce structured fields.

### 3. Mock verification

Use a small mock source layer.

Visible checks:

- PAN
- GST
- Udyam
- Optional MCA / debarment if already stable

### 4. Rule engine

Use normal code for:

- Thresholds
- Dates
- Status checks
- PASS / FAIL / REVIEW

### 5. Evidence dashboard

The officer should see:

- Bidder
- Requirements
- Results
- Issues
- Evidence
- Reason

---

# 6. SHOULD WORK AFTER CORE FLOW

Only add these once the main demo is stable:

- Cross-document discrepancy detection
- Multi-bidder comparison
- Simple audit trail
- Basic role handling

---

# 7. BONUS ONLY

Do not let these delay the core flow:

- Relationship graph
- Advanced anomaly detection
- Document authenticity / tampering analysis
- Complex OCR
- Large number of connectors
- Advanced clarification workflow

---

# 8. What We Are NOT Building for 18 September

Do not spend prototype time on:

- Full production OCR pipeline
- Live government API integrations
- Blockchain implementation
- Enterprise-grade RBAC
- Full MFA infrastructure
- Production malware scanning
- Large-scale historical analytics
- Full anti-collusion forensics
- Kubernetes / microservices
- Advanced vector database infrastructure
- Production deployment architecture

These belong to the full product after selection.

---

# 9. AI Scope for the Prototype

Use AI where it provides obvious value.

## One primary AI workflow

Tender PDF:

```text
Tender text
   ↓
LLM
   ↓
Structured requirements
```

Example:

```json
{
  "requirement": "Minimum annual turnover",
  "threshold": 50000000,
  "operator": ">=",
  "evidence_required": "Audited Financial Statement",
  "mandatory": true
}
```

The rule engine then evaluates the number.

## AI can also generate a simple explanation

Example:

> The bidder's declared turnover differs from the audited financial statement. Manual review is recommended.

Do not ask the LLM to calculate whether ₹4.8 Cr is greater than ₹5 Cr.

---

# 10. Data We Use

For the 18 September demo:

- Synthetic tender
- Synthetic bidder
- Synthetic bidder documents / extracted values
- Mock government verification results

Clearly label mock/synthetic data.

Never imply live government access.

Suggested wording:

> **Government integrations are mocked for the prototype and designed for authorized integration in the full product.**

---

# 11. Suggested Prototype Data

## Tender A

```text
Tender ID: T001

Turnover ≥ ₹5 Cr
GST valid
PAN valid
Udyam valid
OEM authorization required
```

## Tender B

```text
Tender ID: T002

Turnover ≥ ₹3 Cr
GST valid
PAN valid
Udyam valid
```

## Bidder

```text
ABC Technologies Pvt Ltd

PAN: valid
GST: active
Udyam: active

Declared turnover: ₹6.2 Cr
Audited turnover: ₹4.8 Cr

Tender-specific result:
T001 → REVIEW / FAIL
T002 → PASS
```

---

# 12. Recommended Screens

Keep the prototype to roughly 3–4 main screens.

## Screen 1 — Tender

Show:

- Tender name
- Uploaded file
- Extracted requirements

## Screen 2 — Bidder Passport

Show:

- Identity
- GST / PAN / Udyam
- Financial information
- Evidence status
- Key issues

## Screen 3 — Compliance Dashboard

Show:

```text
PASS
FAIL
MANUAL REVIEW
PENDING
```

and the requirement list.

## Screen 4 — Evidence Drill-Down

Click the turnover issue and show:

```text
Requirement
↓
Bidder claim
↓
Evidence
↓
Verification
↓
Rule
↓
Result
↓
Reason
```

If time is tight, combine Screens 2–4.

---

# 13. Team Collaboration

The most important rule:

> **Agree on the data contract before building separately.**

Do not let the frontend, backend and AI layer invent different names for the same fields.

Use one shared structure.

Example:

```json
{
  "tender_id": "T001",
  "requirements": [
    {
      "id": "R01",
      "name": "Minimum Turnover",
      "operator": ">=",
      "threshold": 50000000,
      "mandatory": true,
      "evidence_type": "audited_financials"
    }
  ]
}
```

Bidder:

```json
{
  "bidder_id": "B001",
  "name": "ABC Technologies Pvt Ltd",
  "pan": "VALID",
  "gst": "ACTIVE",
  "udyam": "ACTIVE",
  "declared_turnover": 62000000,
  "verified_turnover": 48000000
}
```

Compliance result:

```json
{
  "requirement_id": "R01",
  "status": "MANUAL_REVIEW",
  "result": "FAIL",
  "value_used": 48000000,
  "reason": "Verified turnover is below the tender threshold and conflicts with the declared value.",
  "evidence": [
    "Self_Declaration.pdf#page=2",
    "Audited_Financials.pdf#page=7"
  ]
}
```

---

# 14. Git / Coding Collaboration Rules

## One repository

Use one shared repository.

Suggested structure:

```text
/apps
  /frontend

/backend
  /api

/ai
  /prompts
  /schemas

/data
  /mock

/docs
```

The exact structure can change.

## Small commits

Commit one meaningful change at a time.

Good:

```text
feat: add tender requirements endpoint
feat: add turnover rule
feat: add bidder passport card
fix: correct compliance status mapping
```

Avoid giant commits containing unrelated work.

## Pull before changing shared files

Before starting work:

```bash
git pull
```

Before pushing:

```bash
git pull --rebase
```

Do not overwrite another teammate's work.

## Shared files

The following should be agreed before changing:

- API response shape
- JSON schemas
- Mock data
- Requirement IDs
- Bidder IDs
- Compliance status names

---

# 15. Team Responsibilities

Adapt these roles to the actual people, but keep ownership clear.

## Prototype / Technical Members

Responsible for:

- Core application flow
- Backend / frontend integration
- AI requirement extraction
- Rule engine
- Mock verification
- Dashboard
- Evidence drill-down

The same members also own the **Technical Approach** part of the pitch.

## Opening / Solution Member

Must understand:

- The GeM registration vs bid-time gap
- What BidTrace does
- Tender-aware compliance
- Bidder Passport
- Evidence-driven investigation
- Human final decision

## Feasibility Member

Must understand:

- Why the technologies are practical
- Which integrations are mocked
- Why AI is selective
- How the prototype can evolve into the full product
- What future authorized integrations would look like

## Impact / Benefits Member

Must understand:

- Manual verification burden
- Faster checking
- Reduced missed inconsistencies
- Better evidence visibility
- Better auditability
- Officer remains in control

Everyone should still know the full workflow.

---

# 16. Communication During the Build

Use one team channel for:

- Current status
- Blockers
- Schema changes
- Integration updates
- Final decisions

Use a simple status format:

```text
DONE:
Tender parser

WORKING:
Compliance API

BLOCKED:
Need frontend field name confirmation

NEXT:
Integrate bidder passport
```

Do not keep important decisions only in private chats.

---

# 17. Integration Contract

Before the frontend and backend are connected, agree on:

### Input

```text
tender_id
bidder_id
requirement_id
```

### Output

```text
status
result
reason
evidence
source
```

Use fixed status values:

```text
PASS
FAIL
PENDING
MANUAL_REVIEW
NOT_APPLICABLE
UNVERIFIABLE
```

Do not rename these halfway through the build.

---

# 18. Failure Strategy

If something breaks close to the demo:

### First priority

Keep the complete core workflow working.

### Second priority

Replace a fragile live calculation with a fixed synthetic result.

### Third priority

Remove bonus features.

Do not risk the main demo for a fancy secondary feature.

---

# 19. Demo Flow

Target roughly 3–5 minutes.

## 0:00–0:30

Explain the problem:

> GeM registration does not answer whether a bidder satisfies the exact requirements of the current tender.

## 0:30–1:00

Upload / open tender.

Show extracted requirements.

## 1:00–1:45

Open bidder passport.

Show verified information.

## 1:45–2:30

Open compliance dashboard.

Show:

```text
PASS
PASS
PASS
REVIEW
```

## 2:30–3:15

Open the turnover contradiction.

Show:

```text
Claim: ₹6.2 Cr
Audited: ₹4.8 Cr
Requirement: ≥ ₹5 Cr

→ Manual review
```

## 3:15–3:45

Show the same bidder against the second tender.

```text
Tender A: ≥ ₹5 Cr → FAIL / REVIEW
Tender B: ≥ ₹3 Cr → PASS
```

## 3:45–4:15

Show the officer evidence trail.

## Closing

> **AI understands. Code verifies. Evidence explains. The officer decides.**

---

# 20. Demo Rules

### Always say

> **Prototype uses synthetic data and mocked government verification sources.**

### Never say

> "We are connected to GST."

unless that is genuinely true and authorized.

### Never say

> "AI rejected the bidder."

Say:

> **"The system identified a compliance issue requiring officer review."**

### Never say

> "This proves collusion."

Say:

> **"This highlights a potential relationship or anomaly for investigation."**

---

# 21. Final Checklist Before Demo

## Product

- Tender loads
- Requirements appear
- Bidder data appears
- Mock verification works
- Rule engine works
- Dashboard works
- Evidence drill-down works
- Bidder Passport works

## Data

- All synthetic values are consistent except the intentional contradiction
- Evidence references are correct
- Requirement IDs are stable
- Demo tender is frozen before rehearsal

## Integration

- Frontend and backend agree on field names
- API responses are stable
- No local-only assumptions remain

## Presentation

Every team member can answer:

1. What problem are we solving?
2. What is BidTrace?
3. What is tender-specific compliance?
4. What is the Bidder Passport?
5. What is AI doing?
6. What is deterministic code doing?
7. What is mocked?
8. Why does the officer remain in control?

---

# 22. The One Rule for 18 September

> **Do not chase feature count. Make one complete workflow work flawlessly.**

The 18 September build is a **proof of concept**.

The real BidTrace platform is defined in the separate **PS 26100 — BidTrace Product Reference Document** and will be expanded after selection.

---

# 23. Separation From the Main Product

### 18 September

```text
Small
Synthetic
Mocked
Focused
Demonstration
```

### Full BidTrace product after selection

```text
Broader evidence intelligence
Full bidder passport
Advanced document intelligence
Cross-source verification
Contradiction analysis
Clarification workflow
Officer investigation desk
Relationship/anomaly analysis
Security and RBAC
Authorized integrations
Auditability
Production architecture
```

Keep these two scopes separate in the team's conversations, pitch preparation and implementation planning.
