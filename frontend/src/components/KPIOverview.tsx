import React from 'react';
import type { AnalyticsSummary } from '../types';
import { ArrowUpRight, Database } from 'lucide-react';

interface KPIOverviewProps {
  summary: AnalyticsSummary | null;
  onSeedData: () => void;
  isSeeding: boolean;
}

export const KPIOverview: React.FC<KPIOverviewProps> = ({ summary, onSeedData, isSeeding }) => {
  if (!summary) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-12) var(--space-6)' }}>
        <p style={{ fontSize: 'var(--text-md)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
          No payment data available.
        </p>
        <button onClick={onSeedData} disabled={isSeeding} className="btn-secondary" style={{ fontSize: 'var(--text-sm)' }}>
          <Database size={14} />
          {isSeeding ? 'Seeding...' : 'Initialize Demo Data'}
        </button>
      </div>
    );
  }

  const recoveryLift = summary.recovery_rate_pct - summary.baseline_recovery_rate_pct;

  const metrics = [
    {
      label: 'Net Incremental Value',
      value: `₹${summary.net_incremental_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      color: 'var(--color-success-text)',
      sub: 'Above baseline, net of costs',
    },
    {
      label: 'Recovery Rate',
      value: `${summary.recovery_rate_pct}%`,
      color: 'var(--text-primary)',
      sub: `+${recoveryLift.toFixed(1)} pp vs ${summary.baseline_recovery_rate_pct}% baseline`,
      badge: true,
    },
    {
      label: 'Recovered Revenue',
      value: `₹${summary.recovered_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      color: 'var(--text-primary)',
      sub: `${summary.recovery_rate_pct}% conversion`,
    },
    {
      label: 'Incremental ROI',
      value: `${summary.roi}x`,
      color: 'var(--color-warning-text)',
      sub: 'Return on intervention cost',
    },
    {
      label: 'Gross Recovery',
      value: `₹${summary.incremental_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      color: 'var(--text-primary)',
      sub: 'Total incremental revenue',
    },
    {
      label: 'Interventions Avoided',
      value: summary.interventions_avoided.toString(),
      color: 'var(--text-primary)',
      sub: 'Customer fatigue prevented',
    },
  ];

  return (
    <div style={{ marginBottom: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-5)' }}>
        <h2 className="page-title">Recovery Overview</h2>
        <button
          onClick={onSeedData}
          disabled={isSeeding}
          className="btn-secondary"
          style={{ fontSize: 'var(--text-sm)', padding: '6px 12px' }}
        >
          <Database size={13} />
          {isSeeding ? 'Seeding...' : 'Re-seed'}
        </button>
      </div>

      {/* Metric grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(6, 1fr)',
        gap: 'var(--space-3)',
      }} className="responsive-grid-3">
        {metrics.map((m, idx) => (
          <div key={idx} className="card" style={{ padding: 'var(--space-4)' }}>
            <div className="label" style={{ marginBottom: 'var(--space-2)' }}>{m.label}</div>
            <div style={{
              fontSize: idx === 0 ? 'var(--text-2xl)' : 'var(--text-xl)',
              fontWeight: 700,
              color: m.color,
              fontFamily: 'var(--font-mono)',
              letterSpacing: '-0.02em',
              marginBottom: '2px',
            }}>
              {m.value}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {m.badge && <ArrowUpRight size={11} style={{ color: 'var(--color-success-text)' }} />}
              {m.sub}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
