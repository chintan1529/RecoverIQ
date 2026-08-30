import React, { useState } from 'react';
import { X, ArrowRight, CheckCircle2, ShieldAlert, UserCheck } from 'lucide-react';
import type { Payment } from '../types';

interface HeroDemoModalProps {
  payments: Payment[];
  onClose: () => void;
  onSelectPayment: (p: Payment) => void;
}

export const HeroDemoModal: React.FC<HeroDemoModalProps> = ({ payments, onClose, onSelectPayment }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const scenarioConfigs = [
    { step: 1, title: 'Smart Delayed Retry', paymentId: 'PAY-HERO-001', context: '₹7,499 Insufficient Funds. 18h delayed retry matches payday window.' },
    { step: 2, title: 'Fatigue Guardrail', paymentId: 'PAY-HERO-002', context: '₹2,499 Auth Failed. 2 contacts in 24h triggers anti-spam block.' },
    { step: 3, title: 'Human Escalation', paymentId: 'PAY-HERO-003', context: '₹85,000 Network Timeout. High-value triggers manual approval.' },
    { step: 4, title: 'Negative ENV → Block', paymentId: 'PAY-HERO-004', context: '₹299 Expired Card. Outreach cost exceeds recovery expectation.' },
  ];

  const currentConfig = scenarioConfigs[currentStep];
  const targetPayment = payments.find((p) => p.payment_id === currentConfig.paymentId) || payments[0];
  const dec = targetPayment?.latest_decision;

  const getStatusBadge = (status?: string) => {
    if (status === 'BLOCK') return <span className="badge badge-red"><ShieldAlert size={10} /> Block</span>;
    if (status === 'RECOMMEND_FOR_APPROVAL') return <span className="badge badge-amber"><UserCheck size={10} /> Approval</span>;
    return <span className="badge badge-green"><CheckCircle2 size={10} /> Auto</span>;
  };

  return (
    <div style={{
      position: 'fixed', bottom: '20px', right: '20px',
      background: 'var(--bg-card)', border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-lg)', width: '420px', padding: 'var(--space-5)',
      boxShadow: 'var(--shadow-lg)', zIndex: 2000,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
        <span className="label" style={{ color: 'var(--color-success-text)' }}>Demo Mode</span>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <X size={16} />
        </button>
      </div>

      {/* Progress */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: 'var(--space-3)' }}>
        {scenarioConfigs.map((_, idx) => (
          <div key={idx} style={{
            flex: 1, height: '3px', borderRadius: '2px',
            background: idx === currentStep ? 'var(--text-primary)' : idx < currentStep ? 'var(--color-success)' : 'var(--border-default)'
          }} />
        ))}
      </div>

      <div style={{ marginBottom: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
          <h4 style={{ fontSize: 'var(--text-md)', fontWeight: 600 }}>{currentConfig.title}</h4>
          {getStatusBadge(dec?.decision_status)}
        </div>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', lineHeight: 1.4 }}>{currentConfig.context}</p>

        {dec && (
          <div style={{ marginTop: 'var(--space-3)', padding: '8px 10px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: 'var(--text-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Action</span>
              <strong style={{ color: 'var(--color-success-text)' }}>{dec.selected_action}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>P(Recovery)</span>
              <strong>{(dec.predicted_recovery_probability * 100).toFixed(1)}% (₹{targetPayment.amount.toLocaleString('en-IN')})</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Net Value</span>
              <strong style={{ color: dec.expected_net_value > 0 ? 'var(--color-success-text)' : 'var(--color-danger-text)' }}>₹{dec.expected_net_value.toLocaleString('en-IN')}</strong>
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px solid var(--border-subtle)', paddingTop: '4px', marginTop: '2px' }}>
              "{dec.explanation.summary}"
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        {targetPayment && (
          <button onClick={() => onSelectPayment(targetPayment)} className="btn-primary"
            style={{ flex: 1, padding: '7px', fontSize: 'var(--text-sm)', justifyContent: 'center' }}>
            Inspect
          </button>
        )}
        <button onClick={() => setCurrentStep((prev) => (prev + 1) % scenarioConfigs.length)} className="btn-secondary"
          style={{ padding: '7px 12px', fontSize: 'var(--text-sm)' }}>
          Next <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
};
