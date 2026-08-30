import React, { useEffect, useState } from 'react';
import type { AgentEvent } from '../types';
import { getAgentActivity, sendRazorpayWebhook } from '../services/api';
import {
  Activity,
  CheckCircle,
  Cpu,
  ShieldCheck,
  Zap,
  Play,
  Pause,
  Layers,
  ChevronRight
} from 'lucide-react';

export const AgentAuditFeed: React.FC = () => {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [filterStage, setFilterStage] = useState<string>('ALL');
  const [selectedEvent, setSelectedEvent] = useState<AgentEvent | null>(null);

  const fetchEvents = () => {
    getAgentActivity().then(setEvents).catch(console.error);
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 4000);
    return () => clearInterval(interval);
  }, []);

  const pipelineNodes = [
    { id: 1, name: 'Ingest', icon: Zap, desc: 'Validate signature & parse payload.' },
    { id: 2, name: 'Features', icon: Layers, desc: 'Assemble 14 pre-decision features.' },
    { id: 3, name: 'Inference', icon: Cpu, desc: 'HistGB leaf scores across actions.' },
    { id: 4, name: 'Calibrate', icon: Activity, desc: 'Platt sigmoid calibration.' },
    { id: 5, name: 'Guardrails', icon: ShieldCheck, desc: 'DNC, anti-spam, suitability.' },
    { id: 6, name: 'Optimize', icon: Activity, desc: 'ENV argmax selection.' },
    { id: 7, name: 'Dispatch', icon: CheckCircle, desc: 'Execute & write audit ledger.' },
  ];

  useEffect(() => {
    let timer: any;
    let nodeTimer: any;
    if (isStreaming) {
      nodeTimer = setInterval(() => {
        setActiveStep((prev) => (prev + 1) % pipelineNodes.length);
      }, 700);
      timer = setInterval(async () => {
        const scenarios = [
          { amount: 450000, error_reason: 'payment_failed_insufficient_funds', error_description: 'Insufficient funds' },
          { amount: 8500000, error_reason: 'payment_timed_out', error_description: 'Bank network timeout' },
          { amount: 1200000, error_reason: 'card_expired', error_description: 'Card has expired' }
        ];
        const sc = scenarios[Math.floor(Math.random() * scenarios.length)];
        try {
          await sendRazorpayWebhook({
            event: 'payment.failed',
            payload: { payment: { entity: {
              id: `pay_stream_${Math.floor(Math.random() * 100000)}`,
              amount: sc.amount, currency: 'INR', method: 'card',
              error_code: 'BAD_REQUEST_ERROR', error_description: sc.error_description,
              error_reason: sc.error_reason, email: 'stream.user@razorpay.demo', contact: '+919988776655'
            }}}
          });
          fetchEvents();
        } catch (e) { console.error(e); }
      }, 3500);
    } else {
      setActiveStep(0);
    }
    return () => { clearInterval(timer); clearInterval(nodeTimer); };
  }, [isStreaming]);

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case 'DECIDE': return <span className="badge badge-blue"><Cpu size={10} /> Decide</span>;
      case 'ACT': return <span className="badge badge-green"><CheckCircle size={10} /> Act</span>;
      case 'APPROVE': return <span className="badge badge-amber"><CheckCircle size={10} /> Approve</span>;
      case 'GUARDRAIL': return <span className="badge badge-amber"><ShieldCheck size={10} /> Guard</span>;
      default: return <span className="badge badge-neutral">{stage}</span>;
    }
  };

  const formatTime = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  };

  const filteredEvents = filterStage === 'ALL' ? events : events.filter((e) => e.stage === filterStage);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 className="page-title">Audit Trace</h2>
          <p className="section-subtitle" style={{ marginTop: '2px' }}>
            End-to-end decision pipeline trace and immutable event ledger.
          </p>
        </div>
        <button
          onClick={() => setIsStreaming(!isStreaming)}
          className={isStreaming ? 'btn-secondary' : 'btn-primary'}
          style={{ fontSize: 'var(--text-sm)', padding: '6px 14px' }}
        >
          {isStreaming ? <Pause size={13} /> : <Play size={13} />}
          {isStreaming ? 'Stop Stream' : 'Start Stream'}
        </button>
      </div>

      {/* Pipeline */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <h3 className="section-title">Decision Pipeline</h3>
          <span style={{ fontSize: 'var(--text-xs)', color: isStreaming ? 'var(--color-success-text)' : 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 500 }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isStreaming ? 'var(--color-success)' : 'var(--text-faint)' }} />
            {isStreaming ? 'Active' : 'Idle'}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '6px' }}>
          {pipelineNodes.map((node, idx) => {
            const Icon = node.icon;
            const isNodeActive = isStreaming && activeStep === idx;
            return (
              <div key={node.id} style={{
                padding: '10px 8px', borderRadius: 'var(--radius-md)',
                background: isNodeActive ? 'var(--color-success-bg)' : 'var(--bg-inset)',
                border: '1px solid', borderColor: isNodeActive ? 'var(--color-success)' : 'var(--border-subtle)',
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                textAlign: 'center', gap: '4px',
                transition: 'all 150ms ease',
              }}>
                <Icon size={14} style={{ color: isNodeActive ? 'var(--color-success-text)' : 'var(--text-muted)' }} />
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)' }}>{node.name}</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.2 }}>{node.desc}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Event Ledger */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            {['ALL', 'DECIDE', 'ACT', 'APPROVE', 'GUARDRAIL'].map((st) => (
              <button key={st} onClick={() => setFilterStage(st)}
                style={{
                  padding: '4px 8px', borderRadius: 'var(--radius-sm)', border: 'none',
                  background: filterStage === st ? 'var(--bg-hover)' : 'transparent',
                  color: filterStage === st ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: 'var(--text-xs)', fontWeight: filterStage === st ? 600 : 400,
                  cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>{st}</button>
            ))}
          </div>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {filteredEvents.length} records
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {filteredEvents.map((evt) => (
            <div key={evt.event_id} onClick={() => setSelectedEvent(evt)}
              style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)', padding: 'var(--space-3) var(--space-4)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                cursor: 'pointer', transition: 'background var(--transition-fast)',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-card)'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                {getStageBadge(evt.stage)}
                <div>
                  <div style={{ fontSize: 'var(--text-base)', fontWeight: 500 }}>{evt.message}</div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '1px' }}>
                    {evt.payment_id} · {evt.event_id}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {formatTime(evt.timestamp)}
                </span>
                <ChevronRight size={14} color="var(--text-faint)" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div onClick={() => setSelectedEvent(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center',
            justifyContent: 'center', zIndex: 1000, padding: 'var(--space-6)'
          }}>
          <div onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)',
              width: '100%', maxWidth: '600px',
            }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
              <div>
                <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 600 }}>Event Record</h3>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{selectedEvent.event_id}</span>
              </div>
              <button onClick={() => setSelectedEvent(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '16px', cursor: 'pointer' }}>
                ✕
              </button>
            </div>
            <div style={{ marginBottom: '10px', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
              {selectedEvent.message}
            </div>
            <pre style={{
              background: 'var(--bg-inset)', padding: '12px', borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--color-interactive-text)',
              maxHeight: '280px', overflowY: 'auto', border: '1px solid var(--border-subtle)'
            }}>
              {JSON.stringify(selectedEvent.metadata_json || {}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
