import { useEffect, useMemo, useState } from 'react';
import { Tender, TenderId, TenderRequirement, ComplianceMatrixItem, Bidder, BackendEvaluationReport } from './types';
import { DemoTab } from './types/ui';
import { apiClient, TenderIntakeResponse, toUiRequirement } from './services/api';
import { Header } from './components/Header';
import { OverviewView } from './components/OverviewView';
import { ComplianceMatrixView } from './components/ComplianceMatrixView';
import { BidderPassportView } from './components/BidderPassportView';
import { ActivityView } from './components/ActivityView';
import { RequirementDrawer } from './components/RequirementDrawer';
import { EvidenceDrawer } from './components/EvidenceDrawer';
import { UploadDocumentModal } from './components/UploadDocumentModal';
import { StartReviewView } from './components/StartReviewView';
import { Toast } from './components/Toast';

const PROJECT_NAME = (import.meta.env.VITE_PROJECT_NAME as string | undefined)?.trim() || 'Saanron';

export default function App() {
  const [currentTab, setCurrentTab] = useState<DemoTab>('overview');
  const [activeTenderId, setActiveTenderId] = useState<TenderId | null>(null);
  const [activeTender, setActiveTender] = useState<Tender | null>(null);
  const [activeRequirements, setActiveRequirements] = useState<TenderRequirement[]>([]);
  const [bidder, setBidder] = useState<Bidder | null>(null);
  const [reports, setReports] = useState<Record<string, BackendEvaluationReport>>({});
  const [reviewedTenderIds, setReviewedTenderIds] = useState<TenderId[]>([]);
  const [backendConnected, setBackendConnected] = useState(false);
  const [backendMode, setBackendMode] = useState('');
  const [booting, setBooting] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedRequirement, setSelectedRequirement] = useState<TenderRequirement | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<ComplianceMatrixItem | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [isToastVisible, setIsToastVisible] = useState(false);

  const showToast = (message: string) => {
    setToastMessage(message);
    setIsToastVisible(true);
    window.setTimeout(() => setIsToastVisible(false), 3500);
  };

  useEffect(() => {
    Promise.all([apiClient.getBidder('BIDDER-001'), apiClient.getHealth()])
      .then(([bidderData, health]) => {
        setBidder(bidderData);
        setBackendConnected(true);
        setBackendMode(health.verification_mode);
      })
      .catch((error) => {
        setBackendConnected(false);
        setLoadError(error instanceof Error ? error.message : 'Unable to reach backend.');
      })
      .finally(() => setBooting(false));
  }, []);

  const handleTenderIntake = (result: TenderIntakeResponse) => {
    setActiveTenderId(result.tender.id);
    setActiveTender(result.tender);
    setActiveRequirements(result.requirements.map(toUiRequirement));
    setReports((current) => ({ ...current, [result.tender.id]: result.evaluation }));
    setReviewedTenderIds((current) => current.includes(result.tender.id) ? current : [...current, result.tender.id]);
    setCurrentTab('overview');
    setSelectedRequirement(null);
    setSelectedEvidence(null);
    setIsUploadModalOpen(false);
    showToast(`${result.tender.title} is ready. Backend evaluation populated ${result.evaluation.requirements.length} requirements.`);
  };

  const handleNewReview = () => {
    setIsUploadModalOpen(true);
  };

  const activeReport = activeTenderId ? reports[activeTenderId] : undefined;

  const updateReport = (tenderId: TenderId, report: BackendEvaluationReport) => {
    setReports((current) => ({ ...current, [tenderId]: report }));
    if (tenderId === activeTenderId) {
      setActiveTender(report.tender);
      setActiveRequirements(report.requirements.map(toUiRequirement));
    }
  };

  const reviewedReports = useMemo(
    () => reviewedTenderIds.map((id) => reports[id]).filter(Boolean),
    [reviewedTenderIds, reports],
  );

  if (booting) {
    return <div className="app-shell"><div className="connection-state"><div><span className="kicker">CASE INTAKE</span><h1>Connecting to the review service</h1><p>Checking the FastAPI workflow before opening the procurement review.</p></div></div></div>;
  }

  return (
    <div className="app-shell">
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        activeTender={activeTender}
        bidderName={bidder?.legal_name}
        backendMode={backendMode}
        backendConnected={backendConnected}
        onNewReview={handleNewReview}
        hasCase={Boolean(activeTender)}
      />

      <div className="app-main">
        {loadError && !backendConnected ? (
          <div className="connection-state connection-error">
            <div><span className="kicker">CONNECTION ERROR</span><h1>Backend connection required</h1><p>{loadError}</p><button type="button" className="primary-action" onClick={() => window.location.reload()}>Retry connection</button></div>
          </div>
        ) : !activeTender || !activeReport ? (
          <StartReviewView onStartReview={handleNewReview} reviewedReports={reviewedReports} onOpenTender={(report) => {
            setActiveTenderId(report.tender.id);
            setActiveTender(report.tender);
            setActiveRequirements(report.requirements.map(toUiRequirement));
            setCurrentTab('overview');
          }} />
        ) : (
          <>
            {currentTab === 'overview' && (
              <OverviewView
                tender={activeTender}
                requirements={activeRequirements}
                report={activeReport}
                reviewedTenderIds={reviewedTenderIds}
                onOpenRequirement={setSelectedRequirement}
                onOpenEvidence={setSelectedEvidence}
                onOpenUpload={handleNewReview}
                onShowToast={showToast}
                onRefreshReport={async () => {
                  const refreshed = await apiClient.checkCompliance(activeTender.id);
                  updateReport(activeTender.id, refreshed);
                }}
              />
            )}
            {currentTab === 'compliance' && <ComplianceMatrixView activeTenderId={activeTender.id} initialReport={activeReport} onReportUpdated={(report) => updateReport(activeTender.id, report)} onOpenEvidencePreview={setSelectedEvidence} onShowToast={showToast} />}
            {currentTab === 'passport' && <BidderPassportView activeTenderId={activeTender.id} reviewedReports={reviewedReports} onShowToast={showToast} />}
            {currentTab === 'activity' && <ActivityView activeTenderId={activeTender.id} onShowToast={showToast} />}
          </>
        )}
      </div>

      <footer className="app-footer"><span>{PROJECT_NAME} · prototype dossier</span><span>Backend-driven · mock sources explicit · officer retains final decision</span></footer>

      <RequirementDrawer requirement={selectedRequirement} tender={activeTender} onClose={() => setSelectedRequirement(null)} />
      <EvidenceDrawer item={selectedEvidence} tenderRef={activeTender?.reference_no || activeTenderId || 'Current case'} bidderName={bidder?.legal_name || 'Selected bidder'} onClose={() => setSelectedEvidence(null)} onShowToast={showToast} onDecisionCommitted={() => setCurrentTab('activity')} />
      <UploadDocumentModal isOpen={isUploadModalOpen} onClose={() => setIsUploadModalOpen(false)} onTenderIntake={handleTenderIntake} onShowToast={showToast} />
      <Toast message={toastMessage} isVisible={isToastVisible} />
    </div>
  );
}
