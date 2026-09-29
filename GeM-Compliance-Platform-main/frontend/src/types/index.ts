export type PageTab =
  | 'tender-requirements'
  | 'bidder-passport'
  | 'compliance-matrix'
  | 'compliance-and-contradictions-result';

export type TenderId = string;

export type ComplianceStatus =
  | 'PASS'
  | 'FAIL'
  | 'MANUAL_REVIEW'
  | 'PENDING'
  | 'UNVERIFIABLE'
  | 'NOT_APPLICABLE';

export interface Tender {
  id: TenderId;
  title: string;
  reference_no: string;
  closing_date: string;
  documents: string[];
  requirements: string[];
  status: string;
  // UI-only display fields are optional because the canonical backend contract does not define them.
  category?: string;
  published_date?: string;
}

/** View model mapped from the canonical backend TenderRequirement. */
export interface TenderRequirement {
  id: string;
  tender_id: TenderId;
  type: 'TURNOVER' | 'GST-STATUS' | 'PAN-STATUS' | 'UDYAM-CHECK' | 'EXPERIENCE' | string;
  rule_code: string;
  title: string;
  description: string;
  operator: string;
  threshold: number | string | null;
  threshold_display: string;
  unit: string;
  mandatory: boolean;
  citation_clause: string;
  citation_page: string;
  source_document_id: string;
  source_page?: number;
  confidence: number;
  rule_id: string;
}

export interface Bidder {
  id: string;
  legal_name: string;
  pan: string;
  gstin: string;
  udyam: string;
  address: string;
  evidence_ids: string[];
}

export interface BackendTenderRequirement {
  id: string;
  tender_id: string;
  type: string;
  title: string;
  description: string;
  operator: string;
  threshold: number | string | null;
  unit: string | null;
  mandatory: boolean;
  source_document_id: string;
  source_page: number;
  confidence: number;
  rule_id: string;
}

export interface BackendEvidence {
  id: string;
  bidder_id: string;
  requirement_id: string;
  document_id: string;
  page: number;
  evidence_type: string;
  field_name: string;
  value: unknown;
  unit?: string | null;
  source_label: string;
  confidence: number;
  verification_status: string;
  notes?: string | null;
}

export interface BackendVerification {
  id: string;
  evidence_id: string;
  source_type: string;
  source_name: string;
  checked_at: string;
  status: string;
  verified_value?: unknown;
  details: string;
}

export interface BackendComplianceResult {
  id: string;
  tender_id: string;
  bidder_id: string;
  requirement_id: string;
  status: ComplianceStatus;
  rule_id: string;
  expected: unknown;
  actual: unknown;
  evidence_ids: string[];
  finding_ids: string[];
  explanation: string;
  evaluated_at: string;
}

export interface BackendAuditEvent {
  id: string;
  timestamp: string;
  actor_type: string;
  action: string;
  tender_id: string;
  bidder_id: string;
  requirement_id?: string | null;
  rule_id?: string | null;
  result_id?: string | null;
  details?: string | null;
  disposition?: string | null;
  note?: string | null;
  sha256_hash?: string | null;
}

export interface BackendEvidenceLink {
  evidence: BackendEvidence;
  document?: Record<string, unknown>;
  page: number;
  extracted_field?: Record<string, unknown>;
  extracted_value?: Record<string, unknown>;
  verifications: BackendVerification[];
}

export interface BackendEvidenceChain {
  requirement: BackendTenderRequirement;
  rule: Record<string, unknown>;
  evidence: BackendEvidenceLink[];
  compliance: BackendComplianceResult;
  audit: BackendAuditEvent | null;
}

export interface BackendEvaluationReport {
  tender: Tender;
  bidder: Bidder;
  requirements: BackendTenderRequirement[];
  passport_verifications: BackendVerification[];
  findings: Array<{
    finding_id: string;
    field_name: string;
    left_field_id: string;
    right_field_id: string;
    left_value: unknown;
    right_value: unknown;
    left_source_label: string;
    right_source_label: string;
    explanation: string;
    requires_manual_review: boolean;
  }>;
  evidence: BackendEvidence[];
  verifications: BackendVerification[];
  compliance_results: BackendComplianceResult[];
  audit_events: BackendAuditEvent[];
  evidence_chains: Record<string, BackendEvidenceChain>;
  summary: Record<string, number>;
}

export interface BidderPassportResponse {
  bidder: Bidder;
  identity: {
    legal_name: string;
    pan: string;
    gstin: string;
    udyam: string;
    address: string;
  };
  evidence: BackendEvidence[];
  verifications: BackendVerification[];
  financial_summary: {
    declared_turnover: number | null;
    declared_turnover_display: string;
    verified_turnover: number | null;
    verified_turnover_display: string;
    variance: number | null;
    variance_display: string;
    audited_document_id: string;
    self_declaration_document_id: string;
  };
  verification_mode: string;
  tender_history?: Array<{
    tender_id: string;
    tender_reference: string;
    tender_title: string;
    evaluated_at: string;
    summary: Record<string, number>;
  }>
}

export interface ComplianceMatrixItem {
  req_id: string;
  rule_spec: string;
  rule_type: string;
  threshold: string;
  actual_extracted: string;
  status: ComplianceStatus;
  document_name: string;
  page_info: string;
  forensic_quote: string;
  is_deviation: boolean;
  pin_color: string;
  result_id: string;
  evidence_ids: string[];
  finding_ids: string[];
  evaluated_at: string;
}

export interface OfficerDecision {
  option: string;
  notes: string;
  timestamp: string;
  sha256_hash: string;
  officer_id: string;
}
