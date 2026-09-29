import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowUpRight, GitBranch, ShieldAlert } from 'lucide-react';
import { ContradictionRadarResponse, TenderId } from '../types';
import { apiClient } from '../services/api';
import { EvidenceCitation, PageFrame, SectionLabel, Stamp } from './DossierUI';

interface Props { activeTenderId: TenderId; bidderName?: string; onShowToast: (message: string) => void; onOpenEvidence: (evidenceId: string) => void; }

const displayValue = (value: unknown) => typeof value === 'number' && value >= 1_000_000 ? `₹${(value / 10_000_000).toFixed(2)} Cr` : String(value ?? '—');

export const ContradictionRadarView: React.FC<Props> = ({ activeTenderId, bidderName, onShowToast, onOpenEvidence }) => {
  const [radar, setRadar] = useState<ContradictionRadarResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient.getContradictionRadar(activeTenderId).then((payload) => { if (!cancelled) setRadar(payload); }).catch((error) => { if (!cancelled) onShowToast(error instanceof Error ? error.message : 'Contradiction Radar unavailable.'); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [activeTenderId, onShowToast]);

  return <PageFrame eyebrow="04 / CONTRADICTION RADAR" title="Surface cross-document inconsistencies" description="The radar aggregates the existing contradiction detector output for the selected bidder. It is an investigation signal, not a fraud finding.">
    <section className="radar-header-grid">
      <div><SectionLabel index="01" meta="CASE">Selected bidder</SectionLabel><h2>{bidderName || 'BIDDER-001'}</h2><p>Scope: {activeTenderId}</p></div>
      <div className="radar-count"><span>Signals</span><strong>{radar?.total ?? '—'}</strong><small>existing contradiction findings</small></div>
      <div className="radar-count"><span>High</span><strong className="text-danger">{radar?.high ?? '—'}</strong><small>linked to a failed deterministic result</small></div>
      <div className="radar-count"><span>Medium</span><strong>{radar?.medium ?? '—'}</strong><small>requires case-file inspection</small></div>
    </section>

    {loading ? <div className="graph-loading"><GitBranch size={16} /> Aggregating contradiction findings…</div> : radar && radar.findings.length > 0 ? <section className="radar-ledger">
      {radar.findings.map((finding, index) => <article key={finding.finding_id} className={`radar-card radar-${finding.severity.toLowerCase()}`}>
        <div className="radar-card-top"><span className="row-index">{String(index + 1).padStart(2, '0')}</span><div><div className="kicker">{finding.severity} · {finding.field_name}</div><h2>{finding.finding_id}</h2></div><Stamp status="MANUAL_REVIEW" /></div>
        <div className="radar-compare"><div><span>{finding.left_source_label}</span><strong>{displayValue(finding.left_value)}</strong></div><div className="radar-versus">≠</div><div><span>{finding.right_source_label}</span><strong>{displayValue(finding.right_value)}</strong></div></div>
        <p>{finding.explanation}</p>
        <div className="radar-links">{finding.evidence_ids.map((id) => <button type="button" key={id} onClick={() => onOpenEvidence(id)}><EvidenceCitation>{id}</EvidenceCitation><ArrowUpRight size={13} /></button>)}{finding.result_ids.map((id) => <span className="radar-result-link" key={id}><ShieldAlert size={13} /> {id}</span>)}</div>
        <div className="radar-footnote"><AlertTriangle size={14} /> This signal does not determine fraud or final eligibility. Follow the linked evidence graph and record the officer disposition separately.</div>
      </article>)}
    </section> : <div className="radar-empty"><ShieldAlert size={17} /><div><strong>No contradictions surfaced for this case.</strong><p>The detector currently has no cross-document discrepancy to aggregate.</p></div></div>}
  </PageFrame>;
};
