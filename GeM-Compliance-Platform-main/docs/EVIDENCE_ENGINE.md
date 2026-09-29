# Evidence Engine

The Evidence Engine is the backend component responsible for converting AI-extracted bidder fields into traceable `Evidence` records and associating `Verification` records with them.

## Responsibilities

- Create `Evidence` from `ExtractedField + Document + TenderRequirement + Bidder`.
- Preserve document ID, source page, field name, value, unit, source label, and extraction confidence.
- Use `ExtractedField.normalized_value` when available so deterministic rules receive normalized data.
- Keep bidder-declared and audited evidence as separate records.
- Attach provider-neutral verification results without changing the shared domain schema.
- Retrieve evidence for a bidder/requirement or document.
- Build a JSON-serializable evidence-chain read model for the frontend/API.
- Support the current prototype with in-memory storage.

## Non-responsibilities

The Evidence Engine does not:

- extract PDF text;
- call the LLM;
- invent requirement or rule IDs;
- decide `PASS`/`FAIL`;
- infer fraud or collusion;
- replace extracted values with verified values;
- implement a live government API.

## Core flow

```text
AI ExtractedField
       +
Bidder + Requirement + Document
       |
       v
EvidenceEngine.create_from_extracted_field()
       |
       v
Evidence (UNVERIFIED)
       |
       v
VerificationConnector.verify()
       |
       v
Verification -> Evidence.verification_status
       |
       v
Deterministic Rule Engine
       |
       v
ComplianceResult
```

## Evidence chain

`build_evidence_chain()` returns a read model containing the existing domain objects in nested form:

```text
Requirement
  -> Rule
  -> Evidence
      -> Document/Page
      -> Extracted Value
      -> Verification(s)
  -> ComplianceResult (optional)
  -> AuditEvent (optional)
```

No new database schema or graph database is required for the prototype.
