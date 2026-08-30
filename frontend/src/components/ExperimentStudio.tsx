import React, { useState } from 'react';
import type { ExperimentResponse } from '../types';
import { runExperiment } from '../services/api';
import { Play, ArrowUpRight } from 'lucide-react';

export const ExperimentStudio: React.FC = () => {
  const [sampleSize, setSampleSize] = useState<number>(2000);
  const [seed, setSeed] = useState<number>(42);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [experiment, setExperiment] = useState<ExperimentResponse | null>(null);

  const handleRunExperiment = async () => {
    setIsRunning(true);
    try {
      const res = await runExperiment(sampleSize, seed);
      setExperiment(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      <div>
        <h2 className="page-title">A/B Experiment Studio</h2>
        <p className="section-subtitle" style={{ marginTop: '2px' }}>
          Counterfactual simulation: Baseline vs RecoverIQ using Common Random Numbers.
        </p>
      </div>

      {/* Controls */}
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 'var(--space-4)', alignItems: 'end' }}>
          <div>
            <label className="label" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>
              Sample Size: <span style={{ color: 'var(--text-primary)' }}>{sampleSize.toLocaleString()}</span>
            </label>
            <input type="range" min={500} max={10000} step={500} value={sampleSize}
              onChange={(e) => setSampleSize(Number(e.target.value))} style={{ width: '100%' }} />
          </div>
          <div>
            <label className="label" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Seed</label>
            <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="input" />
          </div>
          <button onClick={handleRunExperiment} disabled={isRunning} className="btn-primary" style={{ padding: '8px 16px' }}>
            <Play size={13} />
            {isRunning ? 'Running...' : 'Run Experiment'}
          </button>
        </div>
      </div>

      {experiment && (
        <>
          {/* Recovery Rate Comparison */}
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
            <div className="label" style={{ marginBottom: 'var(--space-4)' }}>Recovery Rate Comparison</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-8)' }}>
              <div>
                <div className="metric-hero" style={{ color: 'var(--text-muted)' }}>{experiment.baseline_recovery_rate}%</div>
                <div className="label" style={{ marginTop: 'var(--space-2)' }}>Baseline</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <span className="badge badge-green" style={{ fontSize: 'var(--text-sm)' }}>
                  <ArrowUpRight size={12} /> +{experiment.gross_recovery_lift_pct} pp
                </span>
              </div>
              <div>
                <div className="metric-hero" style={{ color: 'var(--color-success-text)' }}>{experiment.ai_recovery_rate}%</div>
                <div className="label" style={{ marginTop: 'var(--space-2)', color: 'var(--color-success-text)' }}>RecoverIQ</div>
              </div>
            </div>
          </div>

          {/* Impact Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)' }} className="responsive-grid-3">
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Incremental Revenue</div>
              <div className="metric-lg" style={{ color: 'var(--color-success-text)' }}>+₹{experiment.incremental_revenue.toLocaleString('en-IN')}</div>
              {experiment.incremental_revenue_ci_95 && (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '3px' }}>
                  95% CI: [₹{experiment.incremental_revenue_ci_95[0].toLocaleString('en-IN')}, ₹{experiment.incremental_revenue_ci_95[1].toLocaleString('en-IN')}]
                </div>
              )}
            </div>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Net Incremental Value</div>
              <div className="metric-lg" style={{ color: 'var(--text-primary)' }}>₹{experiment.net_incremental_value.toLocaleString('en-IN')}</div>
              {experiment.net_incremental_value_ci_95 && (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '3px' }}>
                  95% CI: [₹{experiment.net_incremental_value_ci_95[0].toLocaleString('en-IN')}, ₹{experiment.net_incremental_value_ci_95[1].toLocaleString('en-IN')}]
                </div>
              )}
            </div>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>ROI</div>
              <div className="metric-lg" style={{ color: 'var(--color-warning-text)' }}>{experiment.roi}x</div>
              {experiment.roi_display_label && (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>{experiment.roi_display_label}</div>
              )}
            </div>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Gross Lift</div>
              <div className="metric-lg" style={{ color: 'var(--color-interactive-text)' }}>+{experiment.gross_recovery_lift_pct} pp</div>
              {experiment.gross_recovery_lift_ci_95 && (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '3px' }}>
                  95% CI: [+{experiment.gross_recovery_lift_ci_95[0]} pp, +{experiment.gross_recovery_lift_ci_95[1]} pp]
                </div>
              )}
            </div>
          </div>

          {/* Side-by-side */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }} className="responsive-grid-2">
            <div className="card">
              <div className="label" style={{ marginBottom: 'var(--space-3)' }}>Baseline Policy</div>
              {[
                { label: 'Recovered Revenue', value: `₹${experiment.baseline_recovered_revenue.toLocaleString('en-IN')}` },
                { label: 'Recovery Rate', value: `${experiment.baseline_recovery_rate}%` },
                { label: 'Costs', value: `₹${experiment.baseline_costs.toLocaleString('en-IN')}` },
                { label: 'Net Value', value: `₹${experiment.baseline_net_value.toLocaleString('en-IN')}`, bold: true },
              ].map((row, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-base)', padding: '4px 0', borderTop: row.bold ? '1px solid var(--border-subtle)' : undefined, marginTop: row.bold ? 'var(--space-2)' : undefined, paddingTop: row.bold ? 'var(--space-2)' : undefined }}>
                  <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                  <span style={{ fontWeight: row.bold ? 700 : 600 }}>{row.value}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <div className="label" style={{ color: 'var(--color-success-text)', marginBottom: 'var(--space-3)' }}>RecoverIQ Policy</div>
              {[
                { label: 'Recovered Revenue', value: `₹${experiment.ai_recovered_revenue.toLocaleString('en-IN')}`, color: 'var(--color-success-text)' },
                { label: 'Recovery Rate', value: `${experiment.ai_recovery_rate}%`, color: 'var(--color-success-text)' },
                { label: 'Costs', value: `₹${experiment.ai_costs.toLocaleString('en-IN')}` },
                { label: 'Net Value', value: `₹${experiment.ai_net_value.toLocaleString('en-IN')}`, color: 'var(--color-success-text)', bold: true },
              ].map((row, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-base)', padding: '4px 0', borderTop: row.bold ? '1px solid var(--border-subtle)' : undefined, marginTop: row.bold ? 'var(--space-2)' : undefined, paddingTop: row.bold ? 'var(--space-2)' : undefined }}>
                  <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                  <span style={{ fontWeight: row.bold ? 700 : 600, color: row.color }}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Methodology */}
          <div style={{ padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>{experiment.methodology || 'Paired Counterfactual with CRN & 500-Iteration Bootstrap 95% CI'}</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>Seed: {experiment.random_seed} · N={experiment.sample_size.toLocaleString()}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
