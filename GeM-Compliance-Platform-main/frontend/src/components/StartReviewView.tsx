import React from 'react';
import { FilePlus2, ArrowRight, Check, History } from 'lucide-react';
import { BackendEvaluationReport } from '../types';
import { SectionLabel, StatusMark } from './DossierUI';

interface Props {
  onStartReview: () => void;
  reviewedReports: BackendEvaluationReport[];
  onOpenTender: (report: BackendEvaluationReport) => void;
}

export const StartReviewView: React.FC<Props> = ({ onStartReview, reviewedReports, onOpenTender }) => (
  <main className="page-frame intake-page">
    <section className="intake-hero">
      <div className="intake-copy">
        <div className="kicker">PROCUREMENT CASE INTAKE · PS 26100</div>
        <h1>Start with the tender document.</h1>
        <p>Open a PDF, let the backend read its clauses, map the supported requirements, and populate a review case against reusable bidder evidence.</p>
        <button type="button" className="primary-action intake-action" onClick={onStartReview}><FilePlus2 size={17} /> Start a new tender review <ArrowRight size={15} /></button>
        <div className="intake-note"><span className="live-dot" /> The supplied prototype PDFs are synthetic demo documents. The review is driven by the uploaded file, not a preloaded tender selector.</div>
      </div>
      <div className="intake-rail">
        <div className="rail-title">REVIEW PATH</div>
        {['Tender document', 'Structured requirements', 'Bidder evidence', 'Verification', 'Deterministic result'].map((label, index) => (
          <div className="rail-step" key={label}><span>{String(index + 1).padStart(2, '0')}</span><div><strong>{label}</strong><small>{index === 0 ? 'PDF enters FastAPI' : index === 1 ? 'Clauses become typed data' : index === 2 ? 'Reusable passport evidence' : index === 3 ? 'Mock source records' : 'Officer-readable outcome'}</small></div>{index < 4 && <div className="rail-line" />}</div>
        ))}
      </div>
    </section>

    {reviewedReports.length > 0 && <section className="recent-cases">
      <SectionLabel index="01" meta={`${reviewedReports.length} REVIEWED`}>Cases opened in this session</SectionLabel>
      <div className="recent-case-ledger">
        {reviewedReports.map((report) => {
          const pass = report.compliance_results.filter((result) => result.status === 'PASS').length;
          const attention = report.compliance_results.length - pass;
          return <button type="button" className="recent-case-row" key={report.tender.id} onClick={() => onOpenTender(report)}>
            <span className="row-index">{report.tender.id}</span>
            <span><strong>{report.tender.title}</strong><small>{report.tender.reference_no} · {report.requirements.length} extracted requirements</small></span>
            <span className="recent-case-result"><StatusMark status={attention ? 'MANUAL_REVIEW' : 'PASS'} compact /><span>{pass}/{report.requirements.length} satisfied</span></span>
          </button>;
        })}
      </div>
    </section>}

    <section className="intake-principles">
      <div><SectionLabel index={reviewedReports.length > 0 ? '02' : '01'} meta="SYSTEM PRINCIPLE">Why this starts with a document</SectionLabel><p><strong>The frontend never decides the compliance result.</strong> It asks the backend for the structured requirements, evidence, verification records and rule evaluation that make up the case.</p></div>
      <div className="principle-quote"><History size={16} /><span>Upload → evaluate → inspect evidence → officer decides</span></div>
    </section>
  </main>
);
