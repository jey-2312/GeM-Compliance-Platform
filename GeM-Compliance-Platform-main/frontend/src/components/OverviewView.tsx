import React, { useMemo } from 'react';
import { FileSearch, RefreshCw, UploadCloud } from 'lucide-react';
import { BackendEvaluationReport, ComplianceMatrixItem, Tender, TenderRequirement } from '../types';
import { toComplianceMatrixItems } from '../services/api';
import { EvidenceCitation, Hairline, MetaItem, QuietButton, SectionLabel, Stamp, StatusMark, TraceLine } from './DossierUI';

interface Props {
  tender: Tender; requirements: TenderRequirement[]; report: BackendEvaluationReport; reviewedTenderIds: string[];
  onOpenRequirement: (requirement: TenderRequirement) => void; onOpenEvidence: (item: ComplianceMatrixItem) => void;
  onOpenUpload: () => void; onShowToast: (message: string) => void; onRefreshReport: () => Promise<void>;
}
const formatNumber = (value: unknown) => typeof value === 'number' ? `₹${(value / 10_000_000).toFixed(2)} Cr` : value == null ? '—' : String(value);

export const OverviewView: React.FC<Props> = ({ tender, requirements, report, reviewedTenderIds, onOpenRequirement, onOpenEvidence, onOpenUpload, onShowToast, onRefreshReport }) => {
  const items = useMemo(() => toComplianceMatrixItems(report), [report]);
  const resultByRequirement = useMemo(() => new Map(items.map((item) => [item.req_id, item])), [items]);
  const attentionItem = items.find((item) => item.status !== 'PASS');
  const attentionRequirement = attentionItem ? report.requirements.find((requirement) => requirement.id === attentionItem.req_id) : undefined;
  const attentionEvidence = attentionItem ? report.evidence.filter((evidence) => attentionItem.evidence_ids.includes(evidence.id)) : [];
  const declaredEvidence = attentionEvidence.find((evidence) => evidence.source_label.toLowerCase().includes('self'));
  const passCount = items.filter((item) => item.status === 'PASS').length;
  const attentionCount = items.length - passCount;

  return <main className="page-frame overview-page">
    <section className="case-hero">
      <div className="case-hero-main">
        <div className="kicker">CASE FILE · {tender.id}</div>
        <h1>{tender.title}</h1>
        <p className="hero-lead">Opened from the uploaded tender document. The backend connected the tender clause, bidder evidence, verification record and deterministic compliance result into this case.</p>
        <div className="hero-meta-row"><MetaItem label="Tender reference" value={tender.reference_no} /><MetaItem label="Bid closing" value={tender.closing_date} /><MetaItem label="Review status" value={<StatusMark status={attentionCount ? 'MANUAL_REVIEW' : 'PASS'} />} /></div>
      </div>
      <div className="case-hero-side"><div className="side-note-title">REVIEW STATUS</div><div className="case-number">{passCount}<span> / </span>{items.length}</div><div className="side-note">requirements currently satisfied by the selected bidder</div><Hairline /><div className="side-note-grid"><div><strong>{attentionCount}</strong><span>requires attention</span></div><div><strong>{report.evidence.length}</strong><span>evidence records</span></div></div></div>
    </section>

    <section className="trace-section"><SectionLabel index="01" meta="BACKEND WORKFLOW">How this case was evaluated</SectionLabel><TraceLine steps={[{ label: 'Tender', detail: 'uploaded PDF recognized', state: 'complete' }, { label: 'Extraction', detail: `${requirements.length} structured clauses`, state: 'complete' }, { label: 'Evidence', detail: 'bidder passport matched', state: 'complete' }, { label: 'Verification', detail: `${report.verifications.length} verification records`, state: 'complete' }, { label: 'Compliance', detail: attentionCount ? `${attentionCount} requires attention` : 'all clear', state: attentionCount ? 'attention' : 'complete' }]} /></section>

    <section className="dossier-section"><SectionLabel index="02" meta={`${requirements.length} CLAUSES`}>Tender requirements</SectionLabel><div className="requirements-ledger">{requirements.map((requirement, index) => { const item = resultByRequirement.get(requirement.id); return <button key={requirement.id} type="button" className={`requirement-row ${item?.status !== 'PASS' ? 'row-attention' : ''}`} onClick={() => onOpenRequirement(requirement)}><span className="row-index">{String(index + 1).padStart(2, '0')}</span><span className="requirement-body"><strong>{requirement.title}</strong><span>{requirement.description}</span><span className="source-line"><EvidenceCitation page={requirement.source_page}>Tender PDF · page {requirement.source_page}</EvidenceCitation><span>·</span><span>{Math.round(requirement.confidence * 100)}% extraction confidence</span></span></span><span className="requirement-result"><span className="threshold-value">{requirement.type === 'TURNOVER' && typeof requirement.threshold === 'number' ? formatNumber(requirement.threshold) : item?.threshold || '—'}</span>{item ? <StatusMark status={item.status} compact /> : <span className="status-mark status-neutral">PENDING</span>}</span></button>; })}</div></section>

    {attentionItem && <section className="finding-section"><div className="finding-copy"><div className="kicker danger-kicker">OFFICER ATTENTION</div><h2>{attentionRequirement?.title || 'Evidence requires review'}</h2><p>The backend found a result that is not a clean pass. Inspect the linked source evidence before recording a disposition.</p>{attentionRequirement?.type === 'TURNOVER' && <div className="comparison-ledger"><div className="comparison-row"><span>Tender minimum</span><strong>{attentionItem.threshold}</strong></div><div className="comparison-row"><span>Self-declared</span><strong>{formatNumber(declaredEvidence?.value)}</strong></div><div className="comparison-row comparison-critical"><span>Audited / verified</span><strong>{attentionItem.actual_extracted}</strong></div></div>}<div className="finding-source"><EvidenceCitation document={attentionItem.document_name} page={attentionItem.page_info.replace(/\D/g, '')}>Source evidence · {attentionItem.page_info}</EvidenceCitation> <span>Result remains traceable to the source document.</span></div></div><div className="finding-action"><Stamp status={attentionItem.status} /><div className="finding-action-label">System result — final officer decision remains outside the rule engine.</div><button type="button" className="primary-action" onClick={() => onOpenEvidence(attentionItem)}><FileSearch size={16} /> Open evidence chain</button></div></section>}

    <section className="closing-section"><div><SectionLabel index="03" meta="DOCUMENT-DRIVEN REVIEW">Next action</SectionLabel><p className="closing-statement"><strong>This case came from a file.</strong> Open another tender to add a new tender-specific evaluation to the bidder passport.</p></div><div className="closing-actions"><QuietButton onClick={() => void onRefreshReport()}><RefreshCw size={14} /> Re-run evaluation</QuietButton><QuietButton tone="dark" onClick={onOpenUpload}><UploadCloud size={14} /> Open another tender</QuietButton></div></section>
  </main>;
};
