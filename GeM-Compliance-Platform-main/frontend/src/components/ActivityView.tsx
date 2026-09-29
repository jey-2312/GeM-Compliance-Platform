import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { BackendAuditEvent, TenderId } from '../types';
import { apiClient } from '../services/api';
import { PageFrame, SectionLabel, StatusMark } from './DossierUI';

interface Props { activeTenderId: TenderId; onShowToast: (message: string) => void; }

const humanize = (value: string) => value.replaceAll('_', ' ').toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());

export const ActivityView: React.FC<Props> = ({ activeTenderId, onShowToast }) => {
  const [events, setEvents] = useState<BackendAuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      await apiClient.checkCompliance(activeTenderId);
      setEvents(await apiClient.getAuditTrail(activeTenderId));
    } catch (error) { onShowToast(error instanceof Error ? error.message : 'Activity unavailable.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [activeTenderId]);

  return (
    <PageFrame eyebrow="04 / ACTIVITY RECORD" title="A chronological system trail" description="Processing, verification, evaluation and officer events are kept in the backend audit trail." actions={<button type="button" className="quiet-button quiet-light" onClick={() => void load()} disabled={loading}><RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh trail <span /></button>}>
      <section className="dossier-section activity-sheet">
        <SectionLabel index="01" meta={`${events.length} EVENTS`}>Case activity</SectionLabel>
        {loading && <div className="empty-state"><Activity size={15} /> Reading audit trail…</div>}
        {!loading && events.length === 0 && <div className="empty-state">No events returned for this case.</div>}
        <div className="timeline">
          {events.slice().reverse().map((event, index) => (
            <article key={`${event.id}-${index}`} className="timeline-event">
              <div className="timeline-marker">{String(index + 1).padStart(2, '0')}</div>
              <div className="timeline-body">
                <div className="timeline-top"><strong>{humanize(event.action)}</strong><time>{new Date(event.timestamp).toLocaleString()}</time></div>
                <p>{event.details || event.note || 'Backend event recorded.'}</p>
                <div className="timeline-meta"><span>{event.actor_type}</span>{event.disposition && <span>{event.disposition}</span>}{event.result_id && <span>result {event.result_id}</span>}</div>
                {event.disposition && <StatusMark status="MANUAL_REVIEW" compact />}
              </div>
            </article>
          ))}
        </div>
      </section>
    </PageFrame>
  );
};
