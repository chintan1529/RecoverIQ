import React, { useState, useEffect } from 'react';
import { Copy, Check } from 'lucide-react';
import { calculateEnterpriseRoi } from '../services/api';
import type { RoiCalculatorResponse } from '../types';

export const EnterpriseRoiCalculator: React.FC = () => {
  const [monthlyGmv, setMonthlyGmv] = useState<number>(50000000);
  const [failureRate, setFailureRate] = useState<number>(12);
  const [aov, setAov] = useState<number>(2500);
  const [marginPct, setMarginPct] = useState<number>(2.0);

  const [roiData, setRoiData] = useState<RoiCalculatorResponse | null>(null);
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const fetchRoi = async () => {
    try {
      const res = await calculateEnterpriseRoi({ monthly_gmv: monthlyGmv, failure_rate_pct: failureRate, aov, margin_pct: marginPct });
      setRoiData(res);
    } catch (err) { console.error('Error calculating ROI:', err); }
  };

  useEffect(() => { fetchRoi(); }, [monthlyGmv, failureRate, aov, marginPct]);

  const copyExecutiveSummary = () => {
    if (!roiData) return;
    const text = `RECOVERIQ ROI PROJECTION:\nMonthly GMV: ₹${(monthlyGmv / 10000000).toFixed(1)} Crore\nFailure Rate: ${failureRate}%\nAnnual Incremental GMV: ₹${(roiData.financial_impact.annual_incremental_gmv / 10000000).toFixed(2)} Crore\nROI: ${roiData.financial_impact.roi_multiplier}x\nPayback: ${roiData.financial_impact.payback_period_days} Days`;
    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 className="page-title">ROI Calculator</h2>
          <p className="section-subtitle" style={{ marginTop: '2px' }}>
            Project annual recovered GMV using empirical bootstrap estimates.
          </p>
        </div>
        <button onClick={copyExecutiveSummary} className="btn-secondary"
          style={{ fontSize: 'var(--text-sm)', padding: '6px 12px' }}>
          {isCopied ? <Check size={13} color="var(--color-success-text)" /> : <Copy size={13} />}
          {isCopied ? 'Copied' : 'Copy Summary'}
        </button>
      </div>

      {/* Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 360px) 1fr', gap: 'var(--space-5)' }}>
        {/* Controls */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <h3 className="section-title">Merchant Parameters</h3>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Monthly GMV</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>₹{(monthlyGmv / 10000000).toFixed(1)} Cr</span>
            </div>
            <input type="range" min={10000000} max={5000000000} step={10000000} value={monthlyGmv}
              onChange={(e) => setMonthlyGmv(Number(e.target.value))} style={{ width: '100%' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              <span>₹1 Cr</span><span>₹500 Cr</span>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Failure Rate</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-danger-text)' }}>{failureRate}%</span>
            </div>
            <input type="range" min={3} max={25} step={1} value={failureRate}
              onChange={(e) => setFailureRate(Number(e.target.value))} style={{ width: '100%' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              <span>3%</span><span>12% avg</span><span>25%</span>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>AOV</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>₹{aov.toLocaleString('en-IN')}</span>
            </div>
            <input type="range" min={500} max={25000} step={500} value={aov}
              onChange={(e) => setAov(Number(e.target.value))} style={{ width: '100%' }} />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Net Margin</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-success-text)' }}>{marginPct}%</span>
            </div>
            <input type="range" min={0.5} max={15.0} step={0.5} value={marginPct}
              onChange={(e) => setMarginPct(Number(e.target.value))} style={{ width: '100%' }} />
          </div>
        </div>

        {/* Output */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {/* Hero metric */}
          <div className="card" style={{ padding: 'var(--space-5)' }}>
            <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Projected Annual Incremental Recovered GMV</div>
            <div style={{ fontSize: 'var(--text-4xl)', fontWeight: 700, color: 'var(--color-success-text)', fontFamily: 'var(--font-mono)', letterSpacing: '-0.03em' }}>
              +₹{roiData ? (roiData.financial_impact.annual_incremental_gmv / 10000000).toFixed(2) : '0.00'} Crore
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
              95% CI: [+₹{roiData ? (roiData.financial_impact.annual_ci_95_gmv[0] / 10000000).toFixed(2) : '0.00'} Cr, +₹{roiData ? (roiData.financial_impact.annual_ci_95_gmv[1] / 10000000).toFixed(2) : '0.00'} Cr]
            </div>
          </div>

          {/* Secondary metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Net Profit Added</div>
              <div className="metric-lg" style={{ color: 'var(--color-interactive-text)' }}>
                +₹{roiData ? (roiData.financial_impact.annual_merchant_net_profit / 100000).toFixed(2) : '0.00'} L
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>Annual bottom line</div>
            </div>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Net Margin ROI</div>
              <div className="metric-lg" style={{ color: 'var(--color-warning-text)' }}>
                {roiData?.financial_impact.roi_multiplier || '—'}x
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>margin profit / spend</div>
            </div>
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Payback Period</div>
              <div className="metric-lg" style={{ color: 'var(--color-success-text)' }}>
                {roiData?.financial_impact.payback_period_days || '—'} days
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>Break-even time</div>
            </div>
          </div>

          {/* Breakdown */}
          <div className="card">
            <h4 className="section-title" style={{ marginBottom: 'var(--space-3)' }}>Financial Breakdown</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              {[
                { label: 'Monthly Failed GMV', value: `₹${roiData ? (roiData.inputs.monthly_failed_gmv / 100000).toFixed(2) : '0.00'} L`, color: 'var(--color-danger-text)' },
                { label: 'Monthly Incremental', value: `+₹${roiData ? (roiData.financial_impact.monthly_incremental_gmv / 100000).toFixed(2) : '0.00'} L`, color: 'var(--color-success-text)' },
                { label: 'Annual Channel Cost', value: `₹${roiData ? (roiData.financial_impact.annual_channel_operating_cost / 100000).toFixed(2) : '0.00'} L`, color: 'var(--text-secondary)' },
                { label: 'Recovered GMV Multiplier', value: `₹${roiData?.financial_impact.gmv_multiplier || '—'} / ₹1 spent`, color: 'var(--color-warning-text)' },
                { label: 'Benchmark Recovery Rate', value: `${roiData?.recovery_rates.baseline_recovery_pct || 33.0}% → ${roiData?.recovery_rates.recoveriq_recovery_pct || 50.2}% (+17.2 pp)`, color: 'var(--color-interactive-text)' },
              ].map((item, i) => (
                <div key={i} style={{ padding: '8px 10px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>{item.label}</span>
                  <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', color: item.color }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
