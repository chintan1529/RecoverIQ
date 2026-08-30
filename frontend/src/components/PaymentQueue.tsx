import React, { useState } from 'react';
import type { Payment } from '../types';
import { CheckCircle, ShieldAlert, ArrowRight, UserCheck } from 'lucide-react';

interface PaymentQueueProps {
  payments: Payment[];
  onSelectPayment: (payment: Payment) => void;
}

export const PaymentQueue: React.FC<PaymentQueueProps> = ({ payments, onSelectPayment }) => {
  const [filterReason, setFilterReason] = useState<string>('ALL');

  const filtered = payments.filter((p) => {
    if (filterReason === 'ALL') return true;
    return p.failure_reason === filterReason;
  });

  const autoCount = payments.filter(p => p.latest_decision?.decision_status === 'AUTO_EXECUTE').length;
  const approvalCount = payments.filter(p => p.latest_decision?.decision_status === 'RECOMMEND_FOR_APPROVAL').length;
  const blockCount = payments.filter(p => p.latest_decision?.decision_status === 'BLOCK').length;
  const pendingCount = payments.filter(p => !p.latest_decision).length;

  const getStatusBadge = (decStatus?: string, execStatus?: string) => {
    if (decStatus === 'BLOCK' || execStatus === 'NOT_EXECUTED') {
      return <span className="badge badge-red"><ShieldAlert size={10} /> Blocked</span>;
    }
    if (decStatus === 'RECOMMEND_FOR_APPROVAL') {
      return <span className="badge badge-amber"><UserCheck size={10} /> Approval</span>;
    }
    if (execStatus === 'EXECUTED') {
      return <span className="badge badge-green"><CheckCircle size={10} /> Executed</span>;
    }
    return <span className="badge badge-blue"><ArrowRight size={10} /> Auto</span>;
  };

  const filterOptions = ['ALL', 'Insufficient Funds', 'Expired Card', 'Network Timeout', 'Authentication Failed'];

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <div>
            <h3 className="section-title">Payment Queue</h3>
            <p className="section-subtitle" style={{ marginTop: '2px' }}>Failed payments scored by Expected Net Value</p>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
            {autoCount > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div className="metric-sm" style={{ color: 'var(--color-interactive-text)' }}>{autoCount}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Auto</div>
              </div>
            )}
            {approvalCount > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div className="metric-sm" style={{ color: 'var(--color-warning-text)' }}>{approvalCount}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Approval</div>
              </div>
            )}
            {blockCount > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div className="metric-sm" style={{ color: 'var(--color-danger-text)' }}>{blockCount}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Blocked</div>
              </div>
            )}
            {pendingCount > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div className="metric-sm" style={{ color: 'var(--text-muted)' }}>{pendingCount}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Pending</div>
              </div>
            )}
          </div>
        </div>

        {/* Filter pills */}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {filterOptions.map((r) => (
            <button
              key={r}
              onClick={() => setFilterReason(r)}
              style={{
                background: filterReason === r ? 'var(--bg-hover)' : 'transparent',
                color: filterReason === r ? 'var(--text-primary)' : 'var(--text-muted)',
                border: 'none',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--text-xs)',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {r === 'ALL' ? 'All' : r}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ paddingLeft: 'var(--space-5)' }}>Payment</th>
              <th>Amount</th>
              <th>Failure</th>
              <th>P(Recovery)</th>
              <th>Exp. Net Value</th>
              <th>Action</th>
              <th>Status</th>
              <th style={{ textAlign: 'right', paddingRight: 'var(--space-5)' }}></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No payments found matching filter "{filterReason === 'ALL' ? 'All' : filterReason}".
                </td>
              </tr>
            ) : (
              filtered.map((p) => {
                const dec = p.latest_decision;
                const isHighValue = p.amount >= 50000;
                return (
                  <tr
                    key={p.payment_id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelectPayment(p)}
                  >
                  <td style={{ paddingLeft: 'var(--space-5)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      {isHighValue && (
                        <span style={{ width: '2px', height: '20px', borderRadius: '1px', background: 'var(--color-warning)', display: 'inline-block', flexShrink: 0 }} />
                      )}
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text-primary)' }}>{p.payment_id}</div>
                        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{p.customer_name}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                      ₹{p.amount.toLocaleString('en-IN')}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      color: 'var(--text-secondary)',
                      fontSize: 'var(--text-xs)',
                    }}>
                      {p.failure_reason}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 600,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 'var(--text-sm)',
                      color: dec ? (dec.predicted_recovery_probability >= 0.6 ? 'var(--color-success-text)' : dec.predicted_recovery_probability >= 0.3 ? 'var(--color-warning-text)' : 'var(--text-muted)') : 'var(--text-faint)',
                    }}>
                      {dec ? `${(dec.predicted_recovery_probability * 100).toFixed(0)}%` : '—'}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 'var(--text-sm)',
                      color: dec ? (dec.expected_net_value > 0 ? 'var(--color-success-text)' : 'var(--color-danger-text)') : 'var(--text-faint)',
                    }}>
                      {dec ? `₹${dec.expected_net_value.toLocaleString('en-IN')}` : '—'}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 'var(--text-base)' }}>
                      {dec ? dec.selected_action : '—'}
                    </span>
                  </td>
                  <td>
                    {getStatusBadge(dec?.decision_status, dec?.execution_status)}
                  </td>
                  <td style={{ textAlign: 'right', paddingRight: 'var(--space-5)' }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); onSelectPayment(p); }}
                      className="btn-ghost"
                      style={{ padding: '4px 8px', fontSize: 'var(--text-xs)', gap: '4px' }}
                    >
                      Inspect <ArrowRight size={11} />
                    </button>
                  </td>
                </tr>
              );
            }))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
