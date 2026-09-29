import React from 'react';
import { Activity, BadgeCheck, ClipboardCheck, FileCheck2, GitBranch, Plus, Radar } from 'lucide-react';
import { Tender } from '../types';
import { DemoTab } from '../types/ui';

interface HeaderProps {
  currentTab: DemoTab;
  onTabChange: (tab: DemoTab) => void;
  activeTender: Tender | null;
  bidderName?: string;
  backendMode?: string;
  backendConnected?: boolean;
  onNewReview: () => void;
  hasCase: boolean;
}

const PROJECT_NAME = (import.meta.env.VITE_PROJECT_NAME as string | undefined)?.trim() || 'Saanron';

const navItems: Array<{ id: DemoTab; label: string; icon: React.ReactNode }> = [
  { id: 'overview', label: 'Case file', icon: <FileCheck2 size={15} /> },
  { id: 'compliance', label: 'Compliance', icon: <ClipboardCheck size={15} /> },
  { id: 'evidence', label: 'Evidence graph', icon: <GitBranch size={15} /> },
  { id: 'contradictions', label: 'Contradiction radar', icon: <Radar size={15} /> },
  { id: 'passport', label: 'Bidder passport', icon: <BadgeCheck size={15} /> },
  { id: 'activity', label: 'Activity', icon: <Activity size={15} /> },
];

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange, activeTender, bidderName, backendMode, backendConnected, onNewReview, hasCase }) => (
  <header className="dossier-header">
    <div className="masthead">
      <div className="brand-lockup">
        <div className="brand-seal" aria-hidden="true"><FileCheck2 size={18} /></div>
        <div>
          <div className="brand-name">{PROJECT_NAME}</div>
          <div className="brand-sub">Procurement review dossier · PS 26100</div>
        </div>
      </div>

      <div className="header-context">
        <div className="header-status">
          <span className={`backend-dot ${backendConnected ? 'is-live' : 'is-down'}`} />
          {backendConnected ? 'FASTAPI CONNECTED' : 'BACKEND OFFLINE'}
        </div>
        {bidderName && <div className="header-bidder">{bidderName}</div>}
      </div>
    </div>

    <div className="masthead-lower">
      <nav className="dossier-nav" aria-label="Primary navigation">
        {navItems.map((item) => (
          <button key={item.id} type="button" onClick={() => onTabChange(item.id)} disabled={!hasCase} className={currentTab === item.id ? 'nav-item nav-active' : 'nav-item'}>
            {item.icon}<span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="case-control">
        {activeTender ? (
          <div className="current-case"><span className="control-caption">CURRENT CASE</span><strong>{activeTender.reference_no} · {activeTender.title}</strong></div>
        ) : <span className="control-caption">NO CASE OPEN</span>}
        <button type="button" className="new-review-button" onClick={onNewReview}><Plus size={14} /> New review</button>
      </div>
    </div>

    <div className="header-rule" />
    <div className="header-footnote">
      <span>Evidence-backed · tender-aware · human-in-the-loop</span>
      <span>{backendConnected ? `Verification mode: ${backendMode || 'configured'}` : 'Connection required'}</span>
    </div>
  </header>
);
