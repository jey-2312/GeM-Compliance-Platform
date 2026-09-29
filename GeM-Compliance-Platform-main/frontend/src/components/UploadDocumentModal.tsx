import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Cpu, FileCheck2, FileUp, X, ArrowRight } from 'lucide-react';
import { apiClient, TenderIntakeResponse } from '../services/api';

interface Props { isOpen: boolean; onClose: () => void; onTenderIntake: (result: TenderIntakeResponse) => void; onShowToast: (msg: string) => void; }

const steps = ['Receive tender PDF', 'Read document', 'Map requirements', 'Evaluate bidder evidence'];

export const UploadDocumentModal: React.FC<Props> = ({ isOpen, onClose, onTenderIntake, onShowToast }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [statusIndex, setStatusIndex] = useState(-1);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState<TenderIntakeResponse | null>(null);

  // A modal component stays mounted between openings. Reset its local state
  // whenever a new review is opened so the previous tender cannot block the
  // next upload (e.g. Tender A -> New Review -> Tender B).
  useEffect(() => {
    if (!isOpen) return;
    setDragging(false);
    setProcessing(false);
    setStatusIndex(-1);
    setStatus('');
    setResult(null);
    if (inputRef.current) inputRef.current.value = '';
  }, [isOpen]);

  if (!isOpen) return null;

  const process = async (file: File) => {
    if (!/\.pdf$/i.test(file.name) && file.type !== 'application/pdf') { onShowToast('Please upload a PDF tender document.'); return; }
    setProcessing(true); setResult(null); setStatusIndex(0); setStatus(`Receiving ${file.name}`);
    try {
      const dataUrl = await fileToDataUrl(file);
      setStatusIndex(1); setStatus('Reading page-aware text through FastAPI…');
      await sleep(220);
      setStatusIndex(2); setStatus('Mapping tender clauses to supported compliance requirements…');
      const response = await apiClient.intakeTenderDocument(dataUrl, file.name, file.type || 'application/pdf');
      setStatusIndex(3); setStatus('Running the deterministic compliance workflow against bidder evidence…');
      await sleep(260);
      setResult(response);
      setStatus('Review ready — the case has been evaluated by the backend.');
    } catch (error) {
      setStatusIndex(-1); setStatus(error instanceof Error ? error.message : 'Tender intake failed.');
      onShowToast(error instanceof Error ? error.message : 'Tender intake failed.');
    } finally { setProcessing(false); }
  };

  return (
    <div className="overlay" onClick={onClose}>
      <div className="paper-modal intake-modal" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-header"><div><div className="kicker">NEW PROCUREMENT REVIEW</div><h2>Open a tender document</h2><p>The uploaded PDF enters the FastAPI intake path. The backend identifies the supported prototype tender, exposes its structured requirements, and runs the seeded bidder evidence through the compliance engine.</p></div><button type="button" className="icon-button" onClick={onClose}><X size={17} /></button></div>
        <div className="modal-body">
          {!result && <>
            <div className={`dropzone ${dragging ? 'dropzone-active' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); const file = event.dataTransfer.files[0]; if (file) void process(file); }} onClick={() => inputRef.current?.click()}>
              <input ref={inputRef} type="file" accept=".pdf,application/pdf" className="visually-hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) void process(file); }} />
              <div className="dropzone-mark"><FileUp size={23} /></div><strong>Drop the tender PDF here</strong><span>Use the supplied Tender_A.pdf or Tender_B.pdf for the controlled prototype workflow.</span>
            </div>
            {status && <div className="intake-progress">
              <div className="progress-header"><span>{processing ? 'PROCESSING CASE' : 'CASE STATUS'}</span><strong>{processing ? 'Backend workflow in progress' : 'Ready'}</strong></div>
              <div className="progress-steps">{steps.map((step, index) => <div key={step} className={`progress-step ${index <= statusIndex ? 'is-done' : ''} ${index === statusIndex && processing ? 'is-current' : ''}`}><span>{index < statusIndex ? <CheckCircle2 size={13} /> : index === statusIndex ? <Cpu size={13} className={processing ? 'spin' : ''} /> : String(index + 1).padStart(2, '0')}</span><div><strong>{step}</strong><small>{index === statusIndex ? status : index < statusIndex ? 'Completed' : 'Waiting'}</small></div></div>)}</div>
            </div>}
          </>}
          {result && <section className="intake-result">
            <div className="result-header"><div><div className="kicker">CASE CREATED FROM DOCUMENT</div><h3>{result.tender.title}</h3><p>{result.tender.reference_no} · {result.file_name}</p></div><div className="result-confirm"><CheckCircle2 size={14} /> Backend evaluated</div></div>
            <div className="intake-result-grid">
              <div><span>Requirements</span><strong>{result.requirements.length}</strong><small>structured clauses</small></div>
              <div><span>PASS</span><strong>{result.evaluation.summary.PASS || 0}</strong><small>requirements satisfied</small></div>
              <div><span>ATTENTION</span><strong>{(result.evaluation.summary.MANUAL_REVIEW || 0) + (result.evaluation.summary.FAIL || 0)}</strong><small>requires inspection</small></div>
              <div><span>TEXT METHOD</span><strong>{result.extraction_method.replace('PYMUPDF+', '')}</strong><small>page-aware extraction</small></div>
            </div>
            <div className="intake-result-note"><FileCheck2 size={15} /><span>Nothing was selected from a tender dropdown. This case was opened from <strong>{result.file_name}</strong>, then evaluated through the backend.</span></div>
            <button type="button" className="primary-action" onClick={() => onTenderIntake(result)}>Open case dossier <ArrowRight size={15} /></button>
          </section>}
        </div>
        {!result && <div className="drawer-footer"><span>Prototype input: synthetic Tender A / Tender B PDFs.</span><button type="button" className="secondary-action" onClick={onClose}>Cancel</button></div>}
      </div>
    </div>
  );
};

const fileToDataUrl = (file: File) => new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Failed to read file.')); reader.readAsDataURL(file); });
const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));
