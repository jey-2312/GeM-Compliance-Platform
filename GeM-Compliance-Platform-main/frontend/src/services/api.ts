import {
  BackendAuditEvent,
  BackendComplianceResult,
  BackendEvidence,
  BackendEvidenceChain,
  BackendEvaluationReport,
  BackendTenderRequirement,
  ContradictionRadarResponse,
  Bidder,
  BidderPassportResponse,
  ComplianceMatrixItem,
  Tender,
  TenderId,
  TenderRequirement,
} from '../types';

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
const API_BASE_URL = (configuredBaseUrl || '/api/v1').replace(/\/$/, '');

export interface DemoSummary { tenders: number; bidders: number; requirements: number; evidence_checks: number; contradictions: number; manual_review_items: number; }

export interface TenderExtractionResponse {
  success: boolean;
  tender: Tender;
  requirements: BackendTenderRequirement[];
  extraction_method: string;
  ocr_used: boolean;
  ai_used: boolean;
  mean_confidence: number | null;
  message: string;
  fallback_used?: boolean;
}

export interface VerificationResponse {
  verified: boolean;
  timestamp: string;
  mode: string;
  source: string;
  verifications: Array<Record<string, unknown>>;
}

export interface CommitDecisionPayload {
  tender_id: string;
  bidder_id: string;
  disposition: string;
  note: string;
}

export interface CommitDecisionResponse {
  success: boolean;
  message: string;
  audit_event: BackendAuditEvent;
}

export interface ExplanationResponse {
  source: string;
  model: string;
  explanation: string;
}

export interface DraftClarificationResponse {
  source: string;
  draft: string;
}


export interface TenderIntakeResponse {
  success: boolean;
  file_name: string;
  tender: Tender;
  requirements: BackendTenderRequirement[];
  evaluation: BackendEvaluationReport;
  extraction_method: string;
  ocr_used: boolean;
  ai_used: boolean;
  mean_confidence: number | null;
  message: string;
}

export interface DocumentProcessResponse {
  success: boolean;
  file_name: string;
  extraction_method: string;
  ocr_used: boolean;
  ai_used: boolean;
  mean_confidence: number | null;
  extracted_requirements: BackendTenderRequirement[];
  message: string;
}

function formatMoney(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value !== 'number') return String(value);
  const crore = value / 10_000_000;
  if (Number.isInteger(crore)) return `₹${crore.toFixed(2)} Crore`;
  return `₹${crore.toFixed(2)} Crore`;
}

function formatExpected(requirement: BackendTenderRequirement): string {
  if (requirement.threshold === null || requirement.threshold === undefined) {
    if (requirement.type === 'GST') return 'ACTIVE';
    if (requirement.type === 'PAN') return 'VALID';
    if (requirement.type === 'UDYAM') return 'ACTIVE';
    return '—';
  }
  if (requirement.unit === 'INR') return formatMoney(requirement.threshold);
  if (requirement.unit === 'PERCENT') return `${requirement.threshold}%`;
  return String(requirement.threshold);
}

function toUiTender(raw: Tender): Tender {
  return {
    ...raw,
    category: raw.category || 'Procurement',
    published_date: raw.published_date || 'Prototype dataset',
  };
}

export function toUiRequirement(raw: BackendTenderRequirement): TenderRequirement {
  const typeMap: Record<string, TenderRequirement['type']> = {
    GST: 'GST-STATUS',
    PAN: 'PAN-STATUS',
    UDYAM: 'UDYAM-CHECK',
  };
  return {
    ...raw,
    type: typeMap[raw.type] || raw.type,
    rule_code: raw.rule_id,
    threshold_display: formatExpected(raw),
    unit: raw.unit || '',
    citation_clause: `Page ${raw.source_page}`,
    citation_page: `Page ${raw.source_page}`,
    source_page: raw.source_page,
  };
}

function extractEvidenceForResult(
  report: BackendEvaluationReport,
  result: BackendComplianceResult,
): BackendEvidence[] {
  return report.evidence.filter((item) => result.evidence_ids.includes(item.id));
}

export function toComplianceMatrixItems(report: BackendEvaluationReport): ComplianceMatrixItem[] {
  const reqMap = new Map<string, BackendTenderRequirement>(report.requirements.map((item) => [item.id, item]));
  return report.compliance_results.map((result) => {
    const requirement = reqMap.get(result.requirement_id);
    const evidence = extractEvidenceForResult(report, result);
    const primary = evidence[0];
    const chain = report.evidence_chains[result.id];
    const link = chain?.evidence?.find((item) => item.evidence.id === primary?.id);
    const threshold = requirement ? formatExpected(requirement) : String(result.expected ?? '—');
    const actualValue = result.actual ?? link?.evidence?.value ?? primary?.value;
    const actualDisplay = requirement?.unit === 'INR' || requirement?.type === 'TURNOVER' ? formatMoney(actualValue) : requirement?.unit === 'PERCENT' ? `${actualValue ?? '—'}%` : String(actualValue ?? '—');
    const forensicQuote = link?.evidence?.notes || result.explanation;

    return {
      req_id: result.requirement_id,
      rule_spec: result.rule_id,
      rule_type: requirement?.type || 'UNKNOWN',
      threshold,
      actual_extracted: actualDisplay,
      status: result.status,
      document_name: primary?.source_label || primary?.document_id || 'No evidence linked',
      page_info: primary ? `Page ${primary.page}` : 'No page evidence',
      forensic_quote: forensicQuote,
      is_deviation: result.status !== 'PASS',
      pin_color: result.status === 'PASS' ? 'emerald' : result.status === 'MANUAL_REVIEW' ? 'amber' : 'rose',
      result_id: result.id,
      evidence_ids: result.evidence_ids,
      finding_ids: result.finding_ids,
      evaluated_at: result.evaluated_at,
      gap_to_compliance: result.gap_to_compliance,
      critical: result.critical,
    };
  });
}

class ProcurementApiClient {
  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: {
          ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
          ...(init?.headers || {}),
        },
      });
    } catch {
      throw new Error(`Unable to reach the FastAPI backend at ${API_BASE_URL}. Start the backend on port 8000 and try again.`);
    }

    const text = await response.text();
    let payload: unknown = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = text;
    }

    if (!response.ok) {
      const rawDetail =
        typeof payload === 'object' && payload !== null && 'detail' in payload
          ? (payload as { detail: unknown }).detail
          : null;
      const detail = typeof rawDetail === 'string' ? rawDetail : rawDetail ? JSON.stringify(rawDetail) : `HTTP ${response.status}`;
      throw new Error(detail);
    }
    return payload as T;
  }


  async getHealth(): Promise<{ verification_mode: string }> {
    return this.request<{ verification_mode: string }>('/health');
  }

  async getDemoSummary(): Promise<DemoSummary> {
    return this.request<DemoSummary>('/demo/summary');
  }

  async resetDemo(): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>('/demo/reset', { method: 'POST' });
  }

  async getTenders(): Promise<Tender[]> {
    const data = await this.request<Tender[]>('/tenders');
    return data.map(toUiTender);
  }

  async getTender(id: TenderId): Promise<Tender> {
    return toUiTender(await this.request<Tender>(`/tenders/${encodeURIComponent(id)}`));
  }

  async getTenderRequirements(tenderId: TenderId): Promise<TenderRequirement[]> {
    const data = await this.request<BackendTenderRequirement[]>(`/tenders/${encodeURIComponent(tenderId)}/requirements`);
    return data.map(toUiRequirement);
  }

  async getBidder(bidderId = 'BIDDER-001'): Promise<Bidder> {
    return this.request<Bidder>(`/bidders/${encodeURIComponent(bidderId)}`);
  }

  async getBidderPassport(bidderId = 'BIDDER-001'): Promise<BidderPassportResponse> {
    return this.request<BidderPassportResponse>(`/bidders/${encodeURIComponent(bidderId)}/passport`);
  }

  async checkCompliance(tenderId: TenderId, bidderId = 'BIDDER-001'): Promise<BackendEvaluationReport> {
    return this.request<BackendEvaluationReport>('/compliance/evaluate', {
      method: 'POST',
      body: JSON.stringify({ tender_id: tenderId, bidder_id: bidderId }),
    });
  }

  async getComplianceResults(tenderId: TenderId, bidderId = 'BIDDER-001') {
    return this.request<BackendComplianceResult[]>(`/compliance/${encodeURIComponent(tenderId)}/${encodeURIComponent(bidderId)}/results`);
  }

  async getEvidenceChain(evidenceId: string): Promise<{ evidence_chain: BackendEvidenceChain }> {
    return this.request<{ evidence_chain: BackendEvidenceChain }>(`/evidence/${encodeURIComponent(evidenceId)}/chain`);
  }

  async getContradictionRadar(tenderId: TenderId, bidderId = 'BIDDER-001'): Promise<ContradictionRadarResponse> {
    return this.request<ContradictionRadarResponse>(`/contradictions/${encodeURIComponent(tenderId)}/${encodeURIComponent(bidderId)}`);
  }

  async commitOfficerDecision(payload: CommitDecisionPayload): Promise<CommitDecisionResponse> {
    return this.request<CommitDecisionResponse>('/audit/commit', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getAuditTrail(tenderId: TenderId, bidderId = 'BIDDER-001'): Promise<BackendAuditEvent[]> {
    const data = await this.request<{ audit_events: BackendAuditEvent[] }>(
      `/compliance/${encodeURIComponent(tenderId)}/${encodeURIComponent(bidderId)}/audit`,
    );
    return data.audit_events;
  }

  async extractTender(tenderId: TenderId, live = false): Promise<TenderExtractionResponse> {
    const suffix = live ? '?mode=live' : '?mode=demo';
    return this.request<TenderExtractionResponse>(`/tenders/${encodeURIComponent(tenderId)}/extract${suffix}`, {
      method: 'POST',
    });
  }

  async verifyBidderStatutory(bidderId = 'BIDDER-001'): Promise<VerificationResponse> {
    return this.request<VerificationResponse>(`/bidders/${encodeURIComponent(bidderId)}/verify`, {
      method: 'POST',
    });
  }

  async explainContradiction(resultId: string): Promise<ExplanationResponse> {
    return this.request<ExplanationResponse>('/ai/explain-contradiction', {
      method: 'POST',
      body: JSON.stringify({ result_id: resultId }),
    });
  }

  async draftClarification(tenderRef: string, bidderName: string, variance: string): Promise<DraftClarificationResponse> {
    return this.request<DraftClarificationResponse>('/ai/draft-clarification', {
      method: 'POST',
      body: JSON.stringify({ tender_ref: tenderRef, bidder_name: bidderName, variance }),
    });
  }


  async intakeTenderDocument(
    fileData: string,
    fileName: string,
    mimeType: string,
  ): Promise<TenderIntakeResponse> {
    return this.request<TenderIntakeResponse>('/reviews/intake', {
      method: 'POST',
      body: JSON.stringify({ file_data: fileData, file_name: fileName, mime_type: mimeType }),
    });
  }

  async uploadAndProcessDocument(
    fileData: string,
    fileName: string,
    mimeType: string,
    documentType = 'TENDER',
  ): Promise<DocumentProcessResponse> {
    return this.request<DocumentProcessResponse>('/documents/ocr-process', {
      method: 'POST',
      body: JSON.stringify({
        file_data: fileData,
        file_name: fileName,
        mime_type: mimeType,
        document_type: documentType,
      }),
    });
  }
}

export const apiClient = new ProcurementApiClient();
