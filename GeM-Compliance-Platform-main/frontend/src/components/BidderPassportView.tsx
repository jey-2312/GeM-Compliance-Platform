import React, { useEffect, useMemo, useState } from 'react';
import { BadgeCheck, RefreshCw, ShieldCheck } from 'lucide-react';
import { BackendEvaluationReport, BidderPassportResponse, TenderId } from '../types';
import { apiClient } from '../services/api';
import { EvidenceCitation, Hairline, MetaItem, PageFrame, SectionLabel, Stamp, StatusMark } from './DossierUI';

interface Props { activeTenderId: TenderId; reviewedReports: BackendEvaluationReport[]; onShowToast: (message: string) => void; }
const formatCr = (value: number | null) => value === null ? '—' : `₹${(value / 10_000_000).toFixed(2)} Cr`;

export const BidderPassportView: React.FC<Props> = ({ activeTenderId, reviewedReports, onShowToast }) => {
  const [passport, setPassport] = useState<BidderPassportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const activeReport = reviewedReports.find((report) => report.tender.id === activeTenderId) || reviewedReports[reviewedReports.length - 1];

  const load = async () => {
    setLoading(true);
    try { setPassport(await apiClient.getBidderPassport('BIDDER-001')); }
    catch (error) { onShowToast(error instanceof Error ? error.message : 'Bidder passport unavailable.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [activeTenderId]);

  const verify = async () => {
    setVerifying(true);
    try { await apiClient.verifyBidderStatutory('BIDDER-001'); onShowToast('Mock statutory verification refreshed through the backend.'); await load(); }
    catch (error) { onShowToast(error instanceof Error ? error.message : 'Verification failed.'); }
    finally { setVerifying(false); }
  };

  const financialRequirement = activeReport?.requirements.find((req) => req.type === 'TURNOVER');
  const financialResult = activeReport?.compliance_results.find((result) => result.requirement_id === financialRequirement?.id);
  const tenderHistory = reviewedReports.map((report) => {
    const turnoverRequirement = report.requirements.find((req) => req.type === 'TURNOVER');
    const turnoverResult = report.compliance_results.find((result) => result.requirement_id === turnoverRequirement?.id);
    return { report, threshold: turnoverRequirement?.threshold ?? null, result: turnoverResult };
  });

  return (
    <PageFrame eyebrow="03 / BIDDER DOSSIER" title="Reusable bidder evidence" description="Identity and source evidence stay with the bidder. Tender-specific requirements are evaluated only when that tender enters the review." actions={<button type="button" className="quiet-button quiet-light" onClick={() => void load()} disabled={loading}><RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh passport <span /></button>}>
      {passport && <>
        <section className="passport-masthead">
          <div className="passport-emblem"><BadgeCheck size={28} /></div>
          <div className="passport-title"><div className="kicker">BIDDER ID · {passport.bidder.id}</div><h2>{passport.bidder.legal_name}</h2><p>{passport.bidder.address}</p></div>
          <div className="passport-proof"><span>Evidence records</span><strong>{passport.evidence.length}</strong><em>{passport.verification_mode.toUpperCase()} SOURCE MODE</em></div>
        </section>

        <section className="dossier-section">
          <SectionLabel index="01" meta="IDENTITY + SOURCE CHECKS">Identity record</SectionLabel>
          <div className="identity-ledger"><MetaItem label="PAN" value={passport.identity.pan} /><MetaItem label="GSTIN" value={passport.identity.gstin} /><MetaItem label="Udyam" value={passport.identity.udyam} /><MetaItem label="Verification mode" value={passport.verification_mode === 'mock' ? 'Mock source (prototype)' : passport.verification_mode} /></div>
          <div className="verification-strip">{['GST', 'PAN', 'UDYAM'].map((kind) => { const verification = passport.verifications.find((item) => item.source_name.toLowerCase().includes(kind.toLowerCase())); return <div key={kind}><span>{kind}</span><StatusMark status={verification?.status || 'PENDING'} compact /><small>{verification?.source_name || 'No record'}</small></div>; })}</div>
          <div className="passport-actions"><button type="button" className="secondary-action" onClick={() => void verify()} disabled={verifying}><ShieldCheck size={15} /> {verifying ? 'Refreshing…' : 'Refresh mock verification'}</button><span>Prototype connector only; production integrations would require authorized sources.</span></div>
        </section>

        <section className="dossier-section">
          <SectionLabel index="02" meta="REUSABLE FINANCIAL EVIDENCE">Financial record</SectionLabel>
          <div className="financial-ledger"><div><span>Self-declared turnover</span><strong>{passport.financial_summary.declared_turnover_display}</strong><EvidenceCitation page="2">Self Declaration · page 2</EvidenceCitation></div><div className="financial-critical"><span>Audited / verified turnover</span><strong>{passport.financial_summary.verified_turnover_display}</strong><EvidenceCitation page="12">Audited Financial Statement · page 12</EvidenceCitation></div><div><span>Variance</span><strong>{passport.financial_summary.variance_display}</strong><small>Preserved as a contradiction signal; not a fraud finding.</small></div></div>
        </section>

        <section className="dossier-section tender-contrast">
          <SectionLabel index="03" meta={reviewedReports.length > 1 ? 'CURRENT + PRIOR REVIEWS' : 'CURRENT TENDER ONLY'}>Tender-specific evaluation history</SectionLabel>
          <div className="current-context-line"><span>Evidence is reusable</span><strong>{activeReport?.tender.title || 'Current tender'}</strong><StatusMark status={financialResult?.status || 'PENDING'} /></div>
          {reviewedReports.length <= 1 && <div className="passport-single-note"><span className="single-note-mark">01</span><div><strong>Only the current tender is in this passport view.</strong><p>Open another tender from the same intake flow and the passport will add a second tender-specific evaluation using the same bidder evidence.</p></div></div>}
          {reviewedReports.length > 1 && <div className="contrast-grid">{tenderHistory.map(({ report, threshold, result }, index) => <React.Fragment key={report.tender.id}><div className="contrast-column"><div className="contrast-head"><span>Review {index + 1} · {report.tender.title}</span><StatusMark status={result?.status || 'PENDING'} /></div><div className="contrast-threshold">Minimum turnover {formatCr(typeof threshold === 'number' ? threshold : null)}</div><div className="contrast-evidence">Verified evidence <strong>{formatCr(passport.financial_summary.verified_turnover)}</strong></div><p>Same bidder evidence, evaluated against this tender's own requirement.</p></div>{index < tenderHistory.length - 1 && <div className="contrast-divider">vs</div>}</React.Fragment>)}</div>}
        </section>

        <section className="passport-note"><Hairline /><p><strong>{reviewedReports.length > 1 ? 'The difference between the reviews is the tender, not the bidder evidence.' : 'This passport is intentionally contextual.'}</strong> It shows only the tender reviews that have actually been opened in this session.</p></section>
      </>}
      {!passport && !loading && <div className="empty-state">Unable to load bidder passport.</div>}
    </PageFrame>
  );
};
