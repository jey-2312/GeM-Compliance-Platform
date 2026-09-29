import React, { useMemo, useState } from 'react';
import { FileText, Loader2, ShieldCheck, X } from 'lucide-react';
import { BackendEvidenceChain, ComplianceStatus, ComplianceMatrixItem } from '../types';
import { apiClient } from '../services/api';
import { EvidenceCitation, Stamp, StatusMark } from './DossierUI';

interface Props { item: ComplianceMatrixItem | null; tenderRef: string; bidderName: string; onClose: () => void; onShowToast: (message: string) => void; onDecisionCommitted: () => void; }

const formatValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') return `₹${(value / 10_000_000).toFixed(2)} Cr`;
  return String(value);
};

export const EvidenceDrawer: React.FC<Props> = ({ item, tenderRef, bidderName, onClose, onShowToast, onDecisionCommitted }) => {
  const [chain, setChain] = useState<BackendEvidenceChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [decision, setDecision] = useState('clarification');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!item?.evidence_ids[0]) { setChain(null); return; }
      setLoading(true);
      try { const response = await apiClient.getEvidenceChain(item.evidence_ids[0]); if (!cancelled) setChain(response.evidence_chain); }
      catch (error) { if (!cancelled) onShowToast(error instanceof Error ? error.message : 'Evidence chain unavailable.'); }
      finally { if (!cancelled) setLoading(false); }
    };
    void load();
    return () => { cancelled = true; };
  }, [item?.evidence_ids, onShowToast]);

  const primaryLink = chain?.evidence?.[0];
  const primaryEvidence = primaryLink?.evidence;
  const verification = useMemo(() => primaryLink?.verifications?.[primaryLink.verifications.length - 1], [primaryLink]);
  const status = chain?.compliance?.status || item?.status || 'PENDING';

  const commit = async () => {
    if (!item || !note.trim()) { onShowToast('Add a short officer note before saving the review event.'); return; }
    setSubmitting(true);
    try {
      await apiClient.commitOfficerDecision({ tender_id: chain?.compliance.tender_id || '', bidder_id: chain?.compliance.bidder_id || '', disposition: decision, note: note.trim() });
      onShowToast('Officer review event saved to the backend audit trail.');
      onDecisionCommitted(); onClose();
    } catch (error) { onShowToast(error instanceof Error ? error.message : 'Unable to save officer review.'); }
    finally { setSubmitting(false); }
  };

  if (!item) return null;

  return (
    <div className="overlay" onClick={onClose}>
      <aside className="paper-drawer evidence-drawer" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-header"><div><div className="kicker">EVIDENCE REVIEW · {item.result_id}</div><h2>{chain?.requirement.title || item.req_id}</h2><p>{bidderName} · {tenderRef}</p></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={17} /></button></div>
        <div className="drawer-body">
          {loading ? <div className="drawer-loading"><Loader2 size={17} className="spin" /> Loading evidence chain…</div> : (
            <>
              <section className="result-banner">
                <div><span className="kicker">BACKEND COMPLIANCE RESULT</span><div className="result-banner-line"><Stamp status={status} /><StatusMark status={status} /></div><p>{chain?.compliance.explanation || item.forensic_quote}</p></div>
              </section>

              <section className="chain-ledger">
                <div className="chain-title">Trace from requirement to result</div>
                <ChainRow number="01" label="Requirement" value={chain?.requirement.description || item.threshold} source={<EvidenceCitation page={chain?.requirement.source_page}>Tender PDF · page {chain?.requirement.source_page || '—'}</EvidenceCitation>} />
                <ChainRow number="02" label="Rule" value={`${chain?.rule?.operator || chain?.requirement.operator || item.rule_spec}`} source={<span className="mono">{item.rule_spec}</span>} />
                <ChainRow number="03" label="Document evidence" value={`${primaryEvidence?.source_label || item.document_name}`} source={<EvidenceCitation page={primaryLink?.page || item.page_info.replace(/\D/g, '')}>page {primaryLink?.page || item.page_info.replace(/\D/g, '') || '—'}</EvidenceCitation>} />
                <ChainRow number="04" label="Extracted value" value={formatValue(primaryEvidence?.value ?? chain?.compliance.actual)} source={<span>{primaryEvidence?.field_name || 'normalized field'}</span>} />
                <ChainRow number="05" label="Verification" value={verification?.status || primaryEvidence?.verification_status || 'Not available'} source={<span>{verification?.source_name || 'verification source'}</span>} />
                <ChainRow number="06" label="Compliance" value={`${formatValue(chain?.compliance.actual)}  vs  ${formatValue(chain?.compliance.expected)}`} source={<span className="mono">deterministic evaluation</span>} status={status} final />
              </section>

              {primaryEvidence && <section className="evidence-source-row"><div><span>Source document</span><strong><FileText size={14} /> {primaryEvidence.source_label}</strong></div><div><span>Confidence</span><strong><ShieldCheck size={14} /> {Math.round((primaryEvidence.confidence || 0) * 100)}%</strong></div></section>}

              {(chain?.requirement.type === 'TURNOVER' || item.rule_type === 'TURNOVER') && <section className="contradiction-ledger"><div className="kicker danger-kicker">CROSS-DOCUMENT CONTRADICTION</div><div className="contradiction-compare"><div><span>Self-declared</span><strong>₹6.20 Cr</strong><EvidenceCitation page="2">Self Declaration · page 2</EvidenceCitation></div><div className="contradiction-arrow">≠</div><div><span>Audited / verified</span><strong>₹4.80 Cr</strong><EvidenceCitation page="12">Audited Financial Statement · page 12</EvidenceCitation></div></div><p>The discrepancy is surfaced as an investigation signal. The prototype does not make a fraud determination.</p></section>}

              <section className="officer-form"><div className="kicker">OFFICER ACTION</div><div className="officer-form-grid"><label><span>Disposition</span><select value={decision} onChange={(event) => setDecision(event.target.value)}><option value="clarification">Request clarification</option><option value="reviewed">Reviewed — no further action</option><option value="escalated">Escalate for further review</option></select></label><label><span>Note</span><textarea value={note} onChange={(event) => setNote(event.target.value)} rows={4} placeholder="Record the next action or context for the case file…" /></label></div></section>
            </>
          )}
        </div>
        <div className="drawer-footer"><div>Evidence source: FastAPI backend · officer action is appended to audit trail.</div><button type="button" className="primary-action" onClick={() => void commit()} disabled={submitting || loading}>{submitting ? 'Saving…' : 'Save officer review'}</button></div>
      </aside>
    </div>
  );
};

const ChainRow = ({ number, label, value, source, status, final }: { number: string; label: string; value: string; source: React.ReactNode; status?: ComplianceStatus | string; final?: boolean }) => (
  <div className={`chain-row ${final ? 'chain-final' : ''}`}><span className="row-index">{number}</span><div className="chain-row-body"><span>{label}</span><strong>{value || '—'}</strong><small>{source}</small></div>{final && <Stamp status={status || 'PENDING'} />}</div>
);
