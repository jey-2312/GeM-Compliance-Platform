import React from 'react';
import { ArrowUpRight, Check, Minus, TriangleAlert } from 'lucide-react';
import { ComplianceStatus } from '../types';

export const PageFrame: React.FC<{ eyebrow: string; title: string; description?: string; actions?: React.ReactNode; children: React.ReactNode }> = ({ eyebrow, title, description, actions, children }) => {
  const sectionNumber = eyebrow.match(/^(\d{2})/)?.[1] || '—';
  const displayEyebrow = eyebrow.replace(/^\d{2}\s*\/\s*/, '');
  return (
  <main className="page-frame">
    <div className="page-heading">
      <div className="section-index">
        <span className="section-number">{sectionNumber}</span>
        <span>{displayEyebrow}</span>
      </div>
      <div className="page-heading-row">
        <div>
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
        {actions && <div className="heading-actions">{actions}</div>}
      </div>
    </div>
    {children}
  </main>
  );
};

export const SectionLabel: React.FC<{ index: string; children: React.ReactNode; meta?: string }> = ({ index, children, meta }) => (
  <div className="section-label-row">
    <div className="section-label"><span>{index}</span>{children}</div>
    {meta && <div className="section-meta">{meta}</div>}
  </div>
);

export const Hairline: React.FC = () => <div className="hairline" />;

export const MetaItem: React.FC<{ label: string; value: React.ReactNode; wide?: boolean }> = ({ label, value, wide }) => (
  <div className={`meta-item ${wide ? 'meta-item-wide' : ''}`}>
    <span className="meta-label">{label}</span>
    <span className="meta-value">{value}</span>
  </div>
);

export const StatusMark: React.FC<{ status: ComplianceStatus | string; compact?: boolean }> = ({ status, compact }) => {
  const normalized = String(status).toUpperCase();
  const kind = normalized === 'PASS' ? 'pass' : normalized === 'FAIL' ? 'fail' : normalized === 'MANUAL_REVIEW' ? 'review' : 'neutral';
  const label = normalized === 'MANUAL_REVIEW' ? 'MANUAL REVIEW' : normalized.replaceAll('_', ' ');
  return <span className={`status-mark status-${kind} ${compact ? 'status-compact' : ''}`}>{label}</span>;
};

export const Stamp: React.FC<{ status: ComplianceStatus | string }> = ({ status }) => {
  const normalized = String(status).toUpperCase();
  const kind = normalized === 'PASS' ? 'pass' : normalized === 'FAIL' ? 'fail' : 'review';
  const label = normalized === 'MANUAL_REVIEW' ? 'REVIEW' : normalized;
  return <div className={`stamp stamp-${kind}`}>{label}</div>;
};

export const EvidenceCitation: React.FC<{ document?: string; page?: string | number; children?: React.ReactNode }> = ({ document, page, children }) => (
  <span className="evidence-citation">
    <span className="citation-mark">[{page ?? '—'}]</span>
    <span>{children || document || 'Source evidence'}</span>
  </span>
);

export const TraceLine: React.FC<{ steps: Array<{ label: string; detail: string; state?: 'complete' | 'attention' | 'pending' }> }> = ({ steps }) => (
  <div className="trace-line">
    {steps.map((step, index) => (
      <React.Fragment key={`${step.label}-${index}`}>
        <div className={`trace-step trace-${step.state || 'complete'}`}>
          <div className="trace-node">{step.state === 'complete' ? <Check size={12} /> : step.state === 'attention' ? <TriangleAlert size={12} /> : <Minus size={12} />}</div>
          <div>
            <div className="trace-label">{step.label}</div>
            <div className="trace-detail">{step.detail}</div>
          </div>
        </div>
        {index < steps.length - 1 && <div className="trace-connector" />}
      </React.Fragment>
    ))}
  </div>
);

export const QuietButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { tone?: 'dark' | 'light' | 'accent' }> = ({ tone = 'light', children, className = '', ...props }) => (
  <button className={`quiet-button quiet-${tone} ${className}`} {...props}>{children}<ArrowUpRight size={14} /></button>
);

export const EmptyState: React.FC<{ label: string }> = ({ label }) => <div className="empty-state">{label}</div>;
