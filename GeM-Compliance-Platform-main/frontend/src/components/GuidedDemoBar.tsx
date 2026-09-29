import React from 'react';
import { ArrowRight, X } from 'lucide-react';
import { BackendEvaluationReport } from '../types';

const STEPS = [
  ['Tender selected', 'Review the extracted clauses, source pages and extraction confidence.'],
  ['Bidder evaluated', 'Open Compliance to see deterministic rule results and the materiality gap.'],
  ['Contradiction surfaced', 'Open the turnover result to inspect the declared-versus-verified discrepancy.'],
  ['Evidence graph', 'Trace clause → requirement → claim → evidence → verification → rule → result → audit.'],
  ['Contradiction radar', 'Aggregate the contradiction detector output and jump back to the linked evidence.'],
  ['Bidder passport', 'Switch views to see the same reusable bidder evidence in context.'],
  ['Officer action', 'Open Activity and commit a reviewed/clarification/escalation disposition.'],
];

export const GuidedDemoBar: React.FC<{ step: number; report: BackendEvaluationReport; onStepChange: (step: number) => void; onExit: () => void; }> = ({ step, report, onStepChange, onExit }) => {
  const current = STEPS[step - 1];
  const done = step > STEPS.length;
  return <div className="guided-demo-bar"><div><span className="kicker">GUIDED DEMO · {Math.min(step, STEPS.length)} / {STEPS.length}</span><strong>{done ? 'Demo complete' : current?.[0]}</strong><small>{done ? 'The evidence-backed review story is ready to replay.' : current?.[1]}</small></div><div className="guided-demo-meta"><span>{report.tender.reference_no}</span>{!done && <button type="button" className="primary-action" onClick={() => onStepChange(step + 1)}>{step === STEPS.length ? 'Finish demo' : 'Next'} <ArrowRight size={14} /></button>}<button type="button" className="icon-button" onClick={onExit} aria-label="Exit guided demo"><X size={16} /></button></div></div>;
};
