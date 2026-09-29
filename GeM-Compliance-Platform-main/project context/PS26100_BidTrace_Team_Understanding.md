# BidTrace — Team Understanding Document

## AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

BidTrace is an AI-assisted platform that helps procurement officers check whether a bidder satisfies the **specific requirements of the specific tender**.

The simplest way to understand the product is:

> **Tender → Understand Requirements → Verify Bidder → Check Compliance → Show Evidence → Officer Decides**

---

# 1. The Problem

A bidder can be registered on GeM and still fail the requirements of a particular tender.

For example, a tender may require:

- Minimum turnover
- Valid GST
- Valid Udyam
- OEM authorization
- Relevant experience
- Local-content percentage
- No current debarment

The information needed to verify these conditions may be spread across many documents and different sources.

The procurement officer has to connect all of this manually.

That is the problem BidTrace is trying to solve.

---

# 2. Our Solution

BidTrace reads the tender, identifies its requirements, collects bidder evidence, verifies the information, checks it against the tender rules and shows the officer the evidence behind the result.

The system is not the final decision-maker.

> **AI assists the officer. The officer makes the final decision.**

---

# 3. The Main Flow

```text
Tender
   ↓
Requirement Extraction
   ↓
Tender Rules
   ↓
Bidder Documents + Source Data
   ↓
Bidder Evidence Passport
   ↓
Verification
   ↓
Cross-Checking
   ↓
Compliance Result
   ↓
Evidence + Explanation
   ↓
Officer Review
```

---

# 4. The Main Features

## Tender Intelligence

AI reads the tender and identifies what the bidder must satisfy.

## Bidder Evidence Passport

Creates a reusable view of the bidder's important evidence such as identity, financials, experience, certificates and verification history.

## Cross-Verification

Compares information across documents and sources.

## Contradiction Radar

Highlights conflicting information.

Example:

```text
Declared turnover: ₹6.2 Cr
Audited turnover:  ₹4.8 Cr

→ Contradiction
```

## Tender-Specific Compliance

The system checks the bidder against the requirements of the current tender.

The same bidder can pass one tender and fail another.

## Evidence Investigation

The officer can trace a result back to the evidence behind it.

```text
Requirement
↓
Evidence
↓
Source
↓
Rule
↓
Result
```

## Officer Investigation Desk

Shows which issues need attention and lets the officer inspect the evidence.

## Relationship / Anomaly Analysis

Can highlight possible relationships or unusual patterns between bidders for further investigation.

---

# 5. Bidder Passport — Our Key Idea

The Bidder Passport is a reusable evidence profile.

Think of it as:

> **One verified evidence profile for the bidder, reused across different tenders.**

Example:

```text
ABC Technologies
Verified turnover: ₹4.8 Cr
```

Tender A:

```text
Requires ≥ ₹5 Cr
→ FAIL / REVIEW
```

Tender B:

```text
Requires ≥ ₹3 Cr
→ PASS
```

This shows an important idea:

> **Compliance depends on the bidder and the tender together.**

---

# 6. What AI Does

AI is useful when the information is difficult for a normal program to understand.

AI can:

- Understand tender language
- Extract requirements
- Understand documents
- Match related information
- Find possible contradictions
- Explain findings

---

# 7. What Normal Code Does

Normal software handles exact rules.

It can:

- Compare numbers
- Check dates
- Check expiry
- Check percentages
- Check status values
- Apply PASS / FAIL rules
- Store records
- Show dashboards

Example:

```text
AI:
"Minimum turnover = ₹5 Cr"

       ↓

Rule Engine:
₹4.8 Cr < ₹5 Cr

       ↓

FAIL
```

The LLM should not be trusted to perform the final arithmetic or compliance logic.

---

# 8. Why Evidence Matters

We do not want the system to only say:

```text
Turnover: FAIL
```

We want:

```text
Requirement:
Turnover ≥ ₹5 Cr

Bidder claim:
₹6.2 Cr

Audited evidence:
₹4.8 Cr

Verification:
₹4.8 Cr

Rule:
Average turnover ≥ ₹5 Cr

Result:
FAIL / MANUAL REVIEW

Reason:
The bidder's declaration conflicts with the audited evidence.
```

The officer can then inspect the actual evidence.

---

# 9. Why the Officer Still Matters

BidTrace is a decision-support system.

It does not automatically:

- Approve a bidder
- Reject a bidder
- Declare fraud
- Confirm collusion

Instead:

```text
AI understands
      ↓
System verifies
      ↓
Evidence explains
      ↓
Officer investigates
      ↓
Officer decides
```

---

# 10. Government Sources

The full product is designed to connect with approved data sources such as:

- PAN / Income Tax
- GST
- Udyam
- MCA
- EPFO / ESIC where relevant
- Debarment / blacklist sources
- Other approved sources

For demonstrations and early development, these can be represented with mock data.

We should always distinguish:

```text
Prototype / Mock
        vs
Authorized Production Integration
```

---

# 11. Security

Because procurement data is sensitive, the full product should include:

- Authentication
- Role-based access
- MFA
- Secure document handling
- File validation
- Audit logs
- Encryption
- Monitoring
- Secure source integrations

Uploaded documents are treated as untrusted input.

A simple rule:

> **Document text is evidence to analyze, not instructions to execute.**

---

# 12. What Happens When Information Is Unclear?

Not every case should become FAIL.

The system can also show:

- Pending
- Manual Review
- Unverifiable
- Not Applicable

For example:

```text
OEM Authorization

AI interpretation:
Medium confidence

→ Manual review
```

This is different from:

```text
Turnover:
₹4.8 Cr

Requirement:
≥ ₹5 Cr

Rule:
FALSE

→ FAIL
```

---

# 13. What the Full Product Looks Like

The final platform is intended to have:

```text
Tender Intelligence
        ↓
Bidder Evidence Passport
        ↓
Cross-Verification
        ↓
Contradiction Radar
        ↓
Compliance Engine
        ↓
Evidence / Explanation
        ↓
Officer Investigation Desk
        ↓
Clarification
        ↓
Final Officer Decision
        ↓
Audit Trail
```

Advanced relationship/anomaly analysis and broader source integrations sit around this core flow.

---

# 14. What Everyone on the Team Should Know

Even if someone is responsible for only one slide, they should understand these five things:

### 1. The problem

Why registration-time verification is not enough.

### 2. The product

What BidTrace actually does.

### 3. The differentiator

Reusable bidder evidence + tender-dependent compliance + investigation-first UX.

### 4. AI vs code

AI understands unstructured information.

Code applies exact rules.

### 5. Human control

The officer makes the final decision.

---

# 15. Our Core Message

The easiest way to remember the project is:

> **GeM verifies at registration. BidTrace verifies at bid-time against the specific tender.**

And:

> **AI understands. Code verifies. Evidence explains. The officer decides.**

---

# 16. What the Different Team Members Need to Focus On

## Solution / Opening

Know:

- Problem
- Core workflow
- Bidder Passport
- Tender-specific compliance
- Why the officer is still in control

## Technical Approach

Know:

- Architecture
- AI vs deterministic rules
- Document processing
- Verification layer
- Compliance engine
- Evidence chain
- Security

## Feasibility

Know:

- Existing technologies
- Why we do not need to train our own foundation model
- Mock connector → authorized integration path
- Prototype → full product progression
- Deployment and security direction

## Impact / Benefits

Know:

- Reduced manual effort
- Faster verification
- Fewer missed inconsistencies
- Better evidence visibility
- Better auditability
- Better support for procurement officers

Everyone should still understand the full product story.

---

# 17. Final Mental Model

Think of BidTrace as five questions:

### 1. What does the tender require?

**Tender Intelligence**

### 2. What does the bidder claim?

**Bidder Evidence Passport**

### 3. Is the evidence trustworthy and consistent?

**Verification + Contradiction Radar**

### 4. Does the bidder satisfy this tender?

**Compliance Engine**

### 5. What should the officer do?

**Evidence + Investigation Desk**

That is the entire project in simple terms.

---

# 18. One-Line Description

> **BidTrace is an evidence-driven tender compliance platform that helps procurement officers verify bidder claims against the exact requirements of a tender and investigate the evidence behind every important result.**
