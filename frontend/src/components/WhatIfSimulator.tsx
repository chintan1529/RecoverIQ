import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Ban,
  UserCheck,
  RefreshCw
} from 'lucide-react';
import { simulateWhatIf } from '../services/api';
import type { WhatIfResponse, PreDecisionFeaturesInput, CandidateActionScore } from '../types';

export const WhatIfSimulator: React.FC = () => {
  const [amount, setAmount] = useState<number>(12500);
  const [failureReason, setFailureReason] = useState<string>('Network Timeout');
  const [paymentMethod, setPaymentMethod] = useState<string>('CreditCard');
  const [customerTier, setCustomerTier] = useState<string>('Gold');
  const [propensityScore, setPropensityScore] = useState<number>(0.75);
  const [consecutiveFailures, setConsecutiveFailures] = useState<number>(1);
  const [contactCount24h, setContactCount24h] = useState<number>(0);
  const [doNotContact, setDoNotContact] = useState<boolean>(false);

  const [simResult, setSimResult] = useState<WhatIfResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const runSimulation = async () => {
    setIsLoading(true);
    try {
      const payload: PreDecisionFeaturesInput = {
        payment_id: 'SIM-PREVIEW',
        customer_id: 'CUST-SIM',
        amount,
        payment_method: paymentMethod,
        failure_reason: failureReason,
        failure_code: 'SIM_ERR',
        customer_tier: customerTier,
        historical_recovery_rate: customerTier === 'Gold' ? 0.65 : 0.40,
        propensity_score: propensityScore,
        contact_count_24h: contactCount24h,
        contact_count_7d: contactCount24h * 2,
        consecutive_failures: consecutiveFailures,
        do_not_contact: doNotContact
      };
      const res = await simulateWhatIf(payload);
      setSimResult(res);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [
    amount, failureReason, paymentMethod, customerTier,
    propensityScore, consecutiveFailures, contactCount24h, doNotContact
  ]);

  const contract = simResult?.contract;
  const attributions = simResult?.attributions;

  const getStatusColor = (status?: string) => {
    if (status === 'BLOCK') return 'var(--color-danger-text)';
    if (status === 'RECOMMEND_FOR_APPROVAL') return 'var(--color-warning-text)';
    return 'var(--color-success-text)';
  };

  const getStatusBg = (status?: string) => {
    if (status === 'BLOCK') return 'var(--color-danger-bg)';
    if (status === 'RECOMMEND_FOR_APPROVAL') return 'var(--color-warning-bg)';
    return 'var(--color-success-bg)';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 className="page-title">What-If Studio</h2>
          <p className="section-subtitle" style={{ marginTop: '2px' }}>
            Perturb failure conditions and observe live calibrated recovery probabilities and ENV decisions.
          </p>
        </div>
        <button
          onClick={runSimulation}
          disabled={isLoading}
          className="btn-secondary"
          style={{ fontSize: 'var(--text-sm)', padding: '6px 12px' }}
        >
          <RefreshCw size={13} />
          Recalculate
        </button>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 360px) 1fr', gap: 'var(--space-5)' }}>
        {/* Left: Parameters */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <h3 className="section-title">Parameters</h3>

          {/* Amount */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Payment Amount</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)', color: amount >= 50000 ? 'var(--color-warning-text)' : 'var(--text-primary)' }}>
                ₹{amount.toLocaleString('en-IN')}
              </span>
            </div>
            <input type="range" min={500} max={150000} step={500} value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              style={{ width: '100%' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              <span>₹500</span><span>₹50k threshold</span><span>₹1.5L</span>
            </div>
          </div>

          {/* Failure Reason */}
          <div>
            <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
              Failure Reason
            </label>
            <select value={failureReason} onChange={(e) => setFailureReason(e.target.value)}
              className="input" style={{ fontSize: 'var(--text-sm)' }}>
              <option value="Network Timeout">Network Timeout</option>
              <option value="Insufficient Funds">Insufficient Funds</option>
              <option value="Expired Card">Expired Card</option>
              <option value="Bank Downtime">Bank Downtime</option>
              <option value="Authentication Failed">Authentication Failed</option>
            </select>
          </div>

          {/* Payment Method */}
          <div>
            <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
              Payment Method
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px' }}>
              {['CreditCard', 'DebitCard', 'UPI', 'NetBanking'].map((m) => (
                <button key={m} onClick={() => setPaymentMethod(m)}
                  style={{
                    padding: '5px 8px', borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    background: paymentMethod === m ? 'var(--bg-hover)' : 'transparent',
                    color: paymentMethod === m ? 'var(--text-primary)' : 'var(--text-muted)',
                    fontSize: 'var(--text-xs)', fontWeight: paymentMethod === m ? 600 : 400,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}>{m}</button>
              ))}
            </div>
          </div>

          {/* Customer Tier */}
          <div>
            <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
              Customer Tier
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px' }}>
              {['Standard', 'Silver', 'Gold', 'Platinum'].map((tier) => (
                <button key={tier} onClick={() => setCustomerTier(tier)}
                  style={{
                    padding: '5px 4px', borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    background: customerTier === tier ? 'var(--bg-hover)' : 'transparent',
                    color: customerTier === tier ? 'var(--text-primary)' : 'var(--text-muted)',
                    fontSize: 'var(--text-xs)', fontWeight: customerTier === tier ? 600 : 400,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}>{tier}</button>
              ))}
            </div>
          </div>

          {/* Propensity */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Propensity Score</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{propensityScore.toFixed(2)}</span>
            </div>
            <input type="range" min={0.10} max={0.99} step={0.05} value={propensityScore}
              onChange={(e) => setPropensityScore(Number(e.target.value))} style={{ width: '100%' }} />
          </div>

          {/* Consecutive Failures */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Consecutive Failures</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)', color: consecutiveFailures >= 3 ? 'var(--color-danger-text)' : 'var(--text-primary)' }}>
                {consecutiveFailures}
              </span>
            </div>
            <input type="range" min={1} max={5} step={1} value={consecutiveFailures}
              onChange={(e) => setConsecutiveFailures(Number(e.target.value))} style={{ width: '100%' }} />
          </div>

          {/* 24h Contact */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-secondary)' }}>Contacts in 24h</label>
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, fontFamily: 'var(--font-mono)', color: contactCount24h >= 2 ? 'var(--color-danger-text)' : 'var(--text-primary)' }}>
                {contactCount24h}
              </span>
            </div>
            <input type="range" min={0} max={4} step={1} value={contactCount24h}
              onChange={(e) => setContactCount24h(Number(e.target.value))} style={{ width: '100%' }} />
          </div>

          {/* DNC Toggle */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '8px 12px', background: doNotContact ? 'var(--color-danger-bg)' : 'var(--bg-inset)',
            border: '1px solid', borderColor: doNotContact ? 'var(--border-strong)' : 'var(--border-default)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: doNotContact ? 'var(--color-danger-text)' : 'var(--text-primary)' }}>
                Do Not Contact
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Hard override</div>
            </div>
            <input type="checkbox" checked={doNotContact} onChange={(e) => setDoNotContact(e.target.checked)}
              style={{ width: '16px', height: '16px', cursor: 'pointer' }} />
          </div>
        </div>

        {/* Right: Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Outcome summary */}
          <div className="card" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 'var(--space-4)'
          }}>
            <div>
              <div className="label" style={{ marginBottom: '2px' }}>Winning Action</div>
              <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700 }}>
                {contract?.selected_action || 'Evaluating...'}
              </div>
            </div>
            <div>
              <div className="label" style={{ marginBottom: '2px' }}>P(Recovery)</div>
              <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-success-text)', fontFamily: 'var(--font-mono)' }}>
                {contract ? `${(contract.predicted_recovery_probability * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div>
              <div className="label" style={{ marginBottom: '2px' }}>Expected Net Value</div>
              <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: (contract?.expected_net_value || 0) > 0 ? 'var(--color-success-text)' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                ₹{contract ? contract.expected_net_value.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '—'}
              </div>
            </div>
            <div>
              <div className="label" style={{ marginBottom: '2px' }}>Status</div>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                padding: '2px 8px', borderRadius: 'var(--radius-sm)',
                background: getStatusBg(contract?.decision_status),
                color: getStatusColor(contract?.decision_status),
                fontSize: 'var(--text-xs)', fontWeight: 600, marginTop: '2px'
              }}>
                {contract?.decision_status === 'BLOCK' && <Ban size={11} />}
                {contract?.decision_status === 'RECOMMEND_FOR_APPROVAL' && <UserCheck size={11} />}
                {contract?.decision_status === 'AUTO_EXECUTE' && <CheckCircle2 size={11} />}
                {contract?.decision_status || 'PENDING'}
              </div>
            </div>
          </div>

          {/* Feature Attribution */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
              <h4 className="section-title">Feature Attribution</h4>
              <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                Base 42.0% → Shift: {attributions ? `${attributions.net_lift_from_base >= 0 ? '+' : ''}${(attributions.net_lift_from_base * 100).toFixed(1)} pp` : '—'}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {attributions?.attributions.map((attr, idx) => (
                <div key={idx} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 60px', alignItems: 'center', gap: '10px' }}>
                  <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {attr.label}
                  </div>
                  <div style={{ position: 'relative', height: '10px', background: 'var(--bg-inset)', borderRadius: '5px', overflow: 'hidden' }}>
                    {attr.direction === 'positive' ? (
                      <div style={{
                        position: 'absolute', left: '50%',
                        width: `${Math.min(50, Math.abs(attr.contribution) * 150)}%`,
                        height: '100%', background: 'var(--color-success)',
                        borderRadius: '0 5px 5px 0'
                      }} />
                    ) : (
                      <div style={{
                        position: 'absolute', right: '50%',
                        width: `${Math.min(50, Math.abs(attr.contribution) * 150)}%`,
                        height: '100%', background: 'var(--color-danger)',
                        borderRadius: '5px 0 0 5px'
                      }} />
                    )}
                    <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', background: 'var(--border-strong)' }} />
                  </div>
                  <div style={{
                    fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', fontWeight: 600,
                    textAlign: 'right',
                    color: attr.direction === 'positive' ? 'var(--color-success-text)' : 'var(--color-danger-text)'
                  }}>
                    {attr.contribution >= 0 ? '+' : ''}{(attr.contribution * 100).toFixed(1)} pp
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Candidate Action Table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--border-subtle)' }}>
              <h4 className="section-title">Candidate Action Ranking</h4>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ paddingLeft: 'var(--space-5)' }}>Action</th>
                    <th>P(Recovery)</th>
                    <th>Exp. Recovery</th>
                    <th>Channel Cost</th>
                    <th>Penalties</th>
                    <th>Net Value</th>
                    <th>Feasibility</th>
                  </tr>
                </thead>
                <tbody>
                  {contract?.candidate_scores.map((cs: CandidateActionScore, idx: number) => {
                    const isSelected = cs.action === contract.selected_action;
                    const totalDeductions = (cs.incentive_cost || 0) + (cs.fatigue_penalty || 0) + (cs.risk_penalty || 0);
                    return (
                      <tr key={idx} style={{
                        background: isSelected ? 'var(--color-success-bg)' : 'transparent',
                        fontWeight: isSelected ? 600 : 400
                      }}>
                        <td style={{ paddingLeft: 'var(--space-5)', color: isSelected ? 'var(--color-success-text)' : 'var(--text-primary)' }}>
                          {cs.action} {isSelected && '(optimal)'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {(cs.predicted_p_recovery * 100).toFixed(1)}%
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          ₹{(cs.expected_recovered_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          ₹{cs.intervention_cost.toFixed(2)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: totalDeductions > 0 ? 'var(--color-warning-text)' : 'var(--text-muted)' }}>
                          {totalDeductions > 0 ? `-₹${totalDeductions.toFixed(2)}` : '₹0.00'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: cs.expected_net_value > 0 ? 'var(--color-success-text)' : 'var(--text-muted)' }}>
                          ₹{cs.expected_net_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td>
                          {cs.is_blocked ? (
                            <span style={{ color: 'var(--color-danger-text)', display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: 'var(--text-xs)' }}>
                              <Ban size={11} /> {cs.block_reason || 'Blocked'}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--color-success-text)', display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: 'var(--text-xs)' }}>
                              <CheckCircle2 size={11} /> Feasible
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Guardrails */}
          <div className="card">
            <h4 className="section-title" style={{ marginBottom: 'var(--space-3)' }}>Guardrail Evaluation</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-2)' }}>
              {contract?.guardrail_results.map((gr, idx) => (
                <div key={idx} style={{
                  padding: '8px 10px', borderRadius: 'var(--radius-md)',
                  background: gr.status === 'BLOCK' ? 'var(--color-danger-bg)' : gr.status === 'ESCALATE' ? 'var(--color-warning-bg)' : 'var(--bg-inset)',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>{gr.guardrail}</span>
                    <span style={{
                      fontSize: '10px', fontWeight: 600, padding: '1px 5px', borderRadius: '3px',
                      background: gr.status === 'BLOCK' ? 'var(--color-danger)' : gr.status === 'ESCALATE' ? 'var(--color-warning)' : 'var(--color-success)',
                      color: '#ffffff'
                    }}>{gr.status}</span>
                  </div>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{gr.reason}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
