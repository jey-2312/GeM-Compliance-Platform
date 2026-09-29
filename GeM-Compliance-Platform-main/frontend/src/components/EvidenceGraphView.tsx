import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, CheckCircle2, FileText, GitBranch, ShieldCheck, XCircle } from 'lucide-react';
import { BackendEvidenceChain, BackendEvaluationReport, ComplianceStatus, TenderId } from '../types';
import { apiClient } from '../services/api';
import { EvidenceCitation, PageFrame, SectionLabel, Stamp } from './DossierUI';

interface Props {
  activeTenderId: TenderId;
  initialReport: BackendEvaluationReport;
  onShowToast: (message: string) => void;
}

type GraphNodeKind = 'clause' | 'requirement' | 'claim' | 'evidence' | 'verification' | 'rule' | 'result' | 'action';
interface GraphNode {
  id: string;
  kind: GraphNodeKind;
  label: string;
  title: string;
  value: string;
  detail: string;
  status?: ComplianceStatus | string;
}

const asDisplay = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') return value >= 1_000_000 ? `₹${(value / 10_000_000).toFixed(2)} Cr` : String(value);
  return String(value);
};

export const EvidenceGraphView: React.FC<Props> = ({ activeTenderId, initialReport, onShowToast }) => {
  const results = initialReport.compliance_results;
  const defaultResult = results.find((item) => item.status === 'FAIL') || results[0];
  const [selectedResultId, setSelectedResultId] = useState(defaultResult?.id || '');
  const [chain, setChain] = useState<BackendEvidenceChain | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState('result');
  const [loading, setLoading] = useState(false);

  const selectedResult = useMemo(() => results.find((item) => item.id === selectedResultId) || results[0], [results, selectedResultId]);
  const loadChain = async (resultId: string) => {
    const result = results.find((item) => item.id === resultId);
    const evidenceId = result?.evidence_ids[0];
    if (!evidenceId) { setChain(null); return; }
    setLoading(true);
    try {
      const response = await apiClient.getEvidenceChain(evidenceId);
      setChain(response.evidence_chain);
      setSelectedNodeId('result');
    } catch (error) {
      onShowToast(error instanceof Error ? error.message : 'Evidence graph unavailable.');
    } finally { setLoading(false); }
  };

  useEffect(() => { if (selectedResultId) void loadChain(selectedResultId); }, [selectedResultId, activeTenderId]);

  const nodes = useMemo<GraphNode[]>(() => {
    if (!chain) return [];
    const evidence = chain.evidence?.[0];
    const verification = evidence?.verifications?.[evidence.verifications.length - 1];
    const claim = evidence?.extracted_value;
    return [
      { id: 'clause', kind: 'clause', label: '01', title: 'Tender clause', value: chain.requirement.description, detail: `Tender PDF · page ${chain.requirement.source_page}` },
      { id: 'requirement', kind: 'requirement', label: '02', title: chain.requirement.title, value: `${chain.requirement.type} · ${chain.requirement.operator}`, detail: `Confidence ${Math.round(chain.requirement.confidence * 100)}%` },
      { id: 'claim', kind: 'claim', label: '03', title: 'Extracted claim', value: asDisplay(claim?.value), detail: `${claim?.field_name || 'structured field'} · source field ${claim?.source_field_id || '—'}` },
      { id: 'evidence', kind: 'evidence', label: '04', title: evidence?.evidence.source_label || 'Evidence', value: evidence ? asDisplay(evidence.evidence.value) : 'No evidence', detail: evidence ? `Document ${evidence.evidence.document_id} · page ${evidence.page}` : 'No linked evidence' },
      { id: 'verification', kind: 'verification', label: '05', title: 'Verification', value: verification?.status || evidence?.evidence.verification_status || 'UNVERIFIED', detail: verification?.source_name || 'No verification record' },
      { id: 'rule', kind: 'rule', label: '06', title: chain.rule.id ? String(chain.rule.id) : 'Deterministic rule', value: String(chain.rule.operator || chain.requirement.operator || '—'), detail: `Field ${String(chain.rule.field || 'document evidence')}` },
      { id: 'result', kind: 'result', label: '07', title: 'Compliance result', value: `${asDisplay(chain.compliance.actual)} vs ${asDisplay(chain.compliance.expected)}`, detail: chain.compliance.explanation, status: chain.compliance.status },
      { id: 'action', kind: 'action', label: '08', title: 'Audit / action', value: chain.audit?.action || 'Awaiting officer action', detail: chain.audit?.details || 'The officer can record the next disposition from the evidence review drawer.' },
    ];
  }, [chain]);

  const selectedNode = nodes.find((node) => node.id === selectedNodeId) || nodes[nodes.length - 2];

  return <PageFrame eyebrow="03 / EVIDENCE GRAPH" title="Follow the proof, not just the result" description="Every node is derived from the existing evidence-chain API. Select a result, then inspect each step from tender clause to audit event.">
    <section className="graph-toolbar">
      <div><SectionLabel index="01" meta={`${results.length} RESULTS`}>Select a compliance result</SectionLabel></div>
      <select value={selectedResult?.id || ''} onChange={(event) => setSelectedResultId(event.target.value)} disabled={loading}>
        {results.map((result) => <option key={result.id} value={result.id}>{result.requirement_id} · {result.status} · {result.rule_id}</option>)}
      </select>
    </section>

    {loading ? <div className="graph-loading"><GitBranch size={16} /> Loading chain…</div> : !chain ? <div className="empty-state">The selected result has no evidence-linked chain yet. Manual-review requirements remain visible in the compliance ledger.</div> : <>
      <section className="evidence-graph-wrap">
        <div className="evidence-graph-line" aria-hidden="true" />
        <div className="evidence-graph-nodes">
          {nodes.map((node, index) => <React.Fragment key={node.id}>
            <button type="button" className={`evidence-graph-node graph-${node.kind} ${selectedNodeId === node.id ? 'is-selected' : ''}`} onClick={() => setSelectedNodeId(node.id)}>
              <span className="graph-node-index">{node.label}</span>
              <span className="graph-node-title">{node.title}</span>
              <strong>{node.value}</strong>
              <small>{node.detail}</small>
              {node.status && <Stamp status={node.status} />}
            </button>
            {index < nodes.length - 1 && <ArrowRight className="graph-arrow" size={16} />}
          </React.Fragment>)}
        </div>
      </section>

      <section className="graph-detail-grid">
        <div className="graph-detail-panel">
          <SectionLabel index="02" meta="SELECTED NODE">Node detail</SectionLabel>
          {selectedNode && <>
            <div className="graph-detail-kicker">{selectedNode.kind.toUpperCase()}</div>
            <h2>{selectedNode.title}</h2>
            <p className="graph-detail-value">{selectedNode.value}</p>
            <p>{selectedNode.detail}</p>
            {selectedNode.id === 'evidence' && chain.evidence[0] && <div className="graph-source-note"><FileText size={14} /><span>{chain.evidence[0].evidence.source_label} · page {chain.evidence[0].page}</span></div>}
            {selectedNode.id === 'verification' && chain.evidence[0]?.verifications?.length > 0 && <div className="graph-source-note"><ShieldCheck size={14} /><span>{chain.evidence[0].verifications[chain.evidence[0].verifications.length - 1].details}</span></div>}
            {selectedNode.id === 'result' && <div className="graph-status-note"><Stamp status={chain.compliance.status} />{chain.compliance.status === 'FAIL' ? <XCircle size={15} /> : <CheckCircle2 size={15} />}<span>{chain.compliance.gap_to_compliance || 'Deterministic result derived from the linked evidence.'}</span></div>}
          </>}
        </div>
        <div className="graph-chain-summary">
          <SectionLabel index="03" meta="PROVENANCE">Source anchors</SectionLabel>
          <div className="graph-source-list">
            <EvidenceCitation page={chain.requirement.source_page}>Tender clause · page {chain.requirement.source_page}</EvidenceCitation>
            {chain.evidence.map((item) => <EvidenceCitation key={item.evidence.id} page={item.page}>{item.evidence.source_label} · page {item.page}</EvidenceCitation>)}
            {chain.audit && <div className="graph-audit-line"><span>{chain.audit.action}</span><small>{chain.audit.timestamp}</small></div>}
          </div>
        </div>
      </section>
    </>}
  </PageFrame>;
};
