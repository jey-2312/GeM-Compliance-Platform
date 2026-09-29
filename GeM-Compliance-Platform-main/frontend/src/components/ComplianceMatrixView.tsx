import React, { useEffect, useMemo, useState } from 'react';
import { RefreshCw, Search } from 'lucide-react';
import { BackendEvaluationReport, ComplianceMatrixItem, TenderId } from '../types';
import { apiClient, toComplianceMatrixItems } from '../services/api';
import { EvidenceCitation, PageFrame, SectionLabel, Stamp, StatusMark } from './DossierUI';

interface Props {
  activeTenderId: TenderId;
  initialReport: BackendEvaluationReport;
  onReportUpdated: (report: BackendEvaluationReport) => void;
  onOpenEvidencePreview: (item: ComplianceMatrixItem) => void;
  onShowToast: (message: string) => void;
}

export const ComplianceMatrixView: React.FC<Props> = ({ activeTenderId, initialReport, onReportUpdated, onOpenEvidencePreview, onShowToast }) => {
  const [report, setReport] = useState<BackendEvaluationReport | null>(initialReport);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'ALL' | 'ATTENTION'>('ALL');

  const evaluate = async () => {
    setLoading(true);
    try { const fresh = await apiClient.checkCompliance(activeTenderId); setReport(fresh); onReportUpdated(fresh); }
    catch (error) { onShowToast(error instanceof Error ? error.message : 'Compliance evaluation failed.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { setReport(initialReport); }, [activeTenderId, initialReport]);

  const allItems = useMemo(() => (report ? toComplianceMatrixItems(report) : []), [report]);
  const items = useMemo(() => allItems.filter((item) => {
    const req = report?.requirements.find((requirement) => requirement.id === item.req_id);
    const haystack = `${req?.title || ''} ${item.actual_extracted} ${item.threshold} ${item.document_name}`.toLowerCase();
    return haystack.includes(query.toLowerCase()) && (filter === 'ALL' || item.status !== 'PASS');
  }), [allItems, filter, query, report]);
  const attention = allItems.filter((item) => item.status !== 'PASS').length;
  const pass = allItems.filter((item) => item.status === 'PASS').length;

  return (
    <PageFrame eyebrow="02 / COMPLIANCE LEDGER" title="Requirement-by-requirement evaluation" description="The table is a view over backend ComplianceResult objects, not a second rule system." actions={
      <button type="button" className="quiet-button quiet-light" onClick={() => void evaluate()} disabled={loading}><RefreshCw size={14} className={loading ? 'spin' : ''} /> Re-run checks <span /></button>
    }>
      <section className="ledger-summary">
        <div><span>Requirements</span><strong>{allItems.length}</strong></div>
        <div><span>Passed</span><strong>{pass}</strong></div>
        <div><span>Attention</span><strong className={attention ? 'text-danger' : ''}>{attention}</strong></div>
        <div className="ledger-summary-note"><span>Selected bidder</span><strong>{report?.bidder.legal_name || '—'}</strong></div>
      </section>

      <section className="filter-strip">
        <div className="filter-toggle">
          <button type="button" onClick={() => setFilter('ALL')} className={filter === 'ALL' ? 'filter-active' : ''}>All</button>
          <button type="button" onClick={() => setFilter('ATTENTION')} className={filter === 'ATTENTION' ? 'filter-active filter-danger' : ''}>Attention</button>
        </div>
        <label className="search-field"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search requirement, evidence or value" /></label>
      </section>

      <section className="compliance-sheet">
        <div className="sheet-head"><span>CLAUSE</span><span>EXPECTED</span><span>EVIDENCE</span><span>RESULT</span><span /></div>
        {items.map((item, index) => {
          const requirement = report?.requirements.find((req) => req.id === item.req_id);
          return (
            <button key={item.result_id} type="button" className={`compliance-row ${item.status !== 'PASS' ? 'compliance-attention' : ''}`} onClick={() => onOpenEvidencePreview(item)}>
              <div className="clause-cell"><span className="row-index">{String(index + 1).padStart(2, '0')}</span><div><strong>{requirement?.title || item.req_id}</strong><span>{requirement?.type || item.rule_type} · <EvidenceCitation page={requirement?.source_page}>page {requirement?.source_page || '—'}</EvidenceCitation></span></div></div>
              <div className="expected-cell">{item.threshold}</div>
              <div className="evidence-cell"><strong>{item.actual_extracted}</strong><span>{item.document_name} · {item.page_info}</span></div>
              <div className="result-cell"><StatusMark status={item.status} /><span className="result-explainer">{item.critical ? 'Critical failure' : item.status === 'PASS' ? 'Rule satisfied' : 'Officer attention'}</span>{item.gap_to_compliance && <small className="gap-note">{item.gap_to_compliance}</small>}</div>
              <div className="chevron-cell">↗</div>
            </button>
          );
        })}
        {!loading && items.length === 0 && <div className="empty-state">No matching requirements.</div>}
        {loading && <div className="empty-state">Running deterministic evaluation…</div>}
      </section>

      <section className="matrix-footnote">
        <Stamp status={attention ? 'MANUAL_REVIEW' : 'PASS'} />
        <p>Review states are not automatic rejection. They identify results whose evidence or comparison should be inspected by the procurement officer.</p>
      </section>
    </PageFrame>
  );
};
