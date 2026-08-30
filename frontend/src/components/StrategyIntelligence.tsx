import React, { useEffect, useState } from 'react';
import type { StrategyPerformance } from '../types';
import { getStrategyPerformance } from '../services/api';

export const StrategyIntelligence: React.FC = () => {
  const [strategies, setStrategies] = useState<StrategyPerformance[]>([]);

  useEffect(() => {
    getStrategyPerformance().then(setStrategies).catch(console.error);
  }, []);

  const segments = [
    {
      title: 'High-Value Recoverable',
      color: 'var(--color-success-text)',
      value: strategies.filter(s => ['Human Escalation', 'Retry Delay 18h'].includes(s.action)).reduce((sum, s) => sum + s.recovered_revenue, 0),
      strategy: 'Human Escalation & Delayed Retries',
    },
    {
      title: 'Payment Method Issues',
      color: 'var(--color-interactive-text)',
      value: strategies.filter(s => s.action === 'Payment Method Update').reduce((sum, s) => sum + s.recovered_revenue, 0),
      strategy: 'Payment Method Update Link',
    },
    {
      title: 'Insufficient Funds',
      color: 'var(--color-warning-text)',
      value: strategies.filter(s => s.action === 'Retry Delay 18h').reduce((sum, s) => sum + s.recovered_revenue, 0),
      strategy: 'Delayed Retry (Payday Window)',
    },
    {
      title: 'High Fatigue / Low Value',
      color: 'var(--color-danger-text)',
      value: strategies.filter(s => s.action === 'Stop Intervention').reduce((sum, s) => sum + s.attempts * 50, 0),
      strategy: 'Stop Intervention (Cost Saved)',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      <div>
        <h2 className="page-title">Strategy Intelligence</h2>
        <p className="section-subtitle" style={{ marginTop: '2px' }}>Recovery value by payment segment and strategy ROI.</p>
      </div>

      {/* Segments */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)' }} className="responsive-grid-3">
        {segments.map((seg) => (
          <div key={seg.title} className="card" style={{ padding: 'var(--space-4)' }}>
            <div className="label" style={{ color: seg.color, marginBottom: 'var(--space-2)' }}>{seg.title}</div>
            <div className="metric-lg" style={{ color: 'var(--text-primary)' }}>
              ₹{seg.value.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>{seg.strategy}</div>
          </div>
        ))}
      </div>

      {/* Strategy Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 className="section-title">Strategy ROI Matrix</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ paddingLeft: 'var(--space-5)' }}>Action</th>
                <th>Decisions</th>
                <th>Recovery Rate</th>
                <th>Revenue</th>
                <th>Cost/Recovery</th>
                <th>ROI</th>
                <th>Best Segment</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s) => (
                <tr key={s.action}>
                  <td style={{ paddingLeft: 'var(--space-5)', fontWeight: 600 }}>{s.action}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{s.attempts}</td>
                  <td style={{ fontWeight: 600, color: 'var(--color-success-text)' }}>{s.recovery_rate_pct}%</td>
                  <td style={{ fontWeight: 600 }}>₹{s.recovered_revenue.toLocaleString('en-IN')}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>₹{s.avg_cost_per_recovery.toFixed(2)}</td>
                  <td style={{ fontWeight: 600, color: 'var(--color-warning-text)' }}>{s.roi}x</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>{s.best_segment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
