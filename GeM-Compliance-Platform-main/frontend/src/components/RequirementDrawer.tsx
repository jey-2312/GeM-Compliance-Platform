import React from 'react';
import { X } from 'lucide-react';
import { Tender, TenderRequirement } from '../types';
import { EvidenceCitation, Stamp } from './DossierUI';

interface Props { requirement: TenderRequirement | null; tender: Tender | null; onClose: () => void; }

export const RequirementDrawer: React.FC<Props> = ({ requirement, tender, onClose }) => {
  if (!requirement || !tender) return null;
  return (
    <div className="overlay" onClick={onClose}>
      <aside className="paper-drawer" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-header"><div><div className="kicker">REQUIREMENT · {requirement.id}</div><h2>{requirement.title}</h2><p>{tender.reference_no} · source page {requirement.source_page}</p></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={17} /></button></div>
        <div className="drawer-body">
          <section className="drawer-lead"><div className="drawer-lead-label">What the tender requires</div><p>{requirement.description}</p><EvidenceCitation page={requirement.source_page}>Tender PDF · page {requirement.source_page}</EvidenceCitation></section>
          <section className="drawer-ledger">
            <div><span>Condition</span><strong>{requirement.mandatory ? 'Mandatory' : 'Optional'}</strong></div>
            <div><span>Threshold</span><strong>{requirement.threshold_display || '—'}</strong></div>
            <div><span>Operator</span><strong>{requirement.operator}</strong></div>
            <div><span>Rule ID</span><strong className="mono">{requirement.rule_id}</strong></div>
            <div><span>Extraction confidence</span><strong>{Math.round(requirement.confidence * 100)}%</strong></div>
          </section>
          <section className="drawer-trace"><div className="kicker">ENTERING THE COMPLIANCE ENGINE</div><div className="drawer-trace-step"><span>01</span><strong>Document understanding</strong><p>AI/document extraction turns tender language into structured data.</p></div><div className="drawer-trace-step"><span>02</span><strong>Shared requirement</strong><p>The normalized requirement is carried into the backend domain model.</p></div><div className="drawer-trace-step"><span>03</span><strong>Deterministic rule</strong><p>The evaluator uses the rule ID and structured threshold to produce the final result.</p></div></section>
          <div className="drawer-endmark"><Stamp status="PASS" /><p>This panel explains the source contract only. It does not itself calculate compliance.</p></div>
        </div>
      </aside>
    </div>
  );
};
