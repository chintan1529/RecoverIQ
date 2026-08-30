import React, { useState, useEffect } from 'react';
import type { Payment, DecisionContract, CandidateActionScore, AttributionsResult } from '../types';
import { evaluatePayment, executePaymentSimulation, approvePaymentDecision, rejectPaymentDecision, getPaymentAttributions } from '../services/api';
import { X, Play, ShieldCheck, Cpu, Sparkles, UserCheck, ArrowRight, CheckCircle2, Ban, XCircle } from 'lucide-react';

interface PaymentDetailStudioProps {
  payment: Payment;
  onClose: () => void;
  onRefresh: () => void;
}

export const PaymentDetailStudio: React.FC<PaymentDetailStudioProps> = ({ payment, onClose, onRefresh }) => {
  const [dec, setDec] = useState<DecisionContract | undefined>(payment.latest_decision);
  const [attributions, setAttributions] = useState<AttributionsResult | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [execMessage, setExecMessage] = useState<string | null>(null);

  useEffect(() => {
    if (payment.payment_id) {
      getPaymentAttributions(payment.payment_id)
        .then(setAttributions)
        .catch(() => {
          // Fallback if not evaluated yet
          setAttributions(null);
        });
    }
  }, [payment.payment_id, dec]);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    try {
      const contract = await evaluatePayment(payment.payment_id);
      setDec(contract);
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      const res = await executePaymentSimulation(payment.payment_id);
      setExecMessage(res.message);
      onRefresh();
    } catch (err: any) {
      setExecMessage(err.response?.data?.detail || 'Execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApprove = async () => {
    try {
      await approvePaymentDecision(payment.payment_id);
      setExecMessage('Decision approved by operator');
      handleEvaluate();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleReject = async () => {
    try {
      await rejectPaymentDecision(payment.payment_id);
      setExecMessage('Decision rejected by operator');
      handleEvaluate();
    } catch (err: any) {
      console.error(err);
    }
  };

  const getScoreForAction = (action: string): CandidateActionScore | undefined => {
    if (!dec?.candidate_scores) return undefined;
    return dec.candidate_scores.find((s) => s.action === action);
  };


  const statusColor = dec?.decision_status === 'BLOCK' ? 'var(--color-rose)' : dec?.decision_status === 'RECOMMEND_FOR_APPROVAL' ? 'var(--color-amber)' : 'var(--color-emerald)';
  const statusBg = dec?.decision_status === 'BLOCK' ? 'var(--color-rose-bg)' : dec?.decision_status === 'RECOMMEND_FOR_APPROVAL' ? 'var(--color-amber-bg)' : 'var(--color-emerald-bg)';
  const statusBorder = dec?.decision_status === 'BLOCK' ? 'var(--color-rose-border)' : dec?.decision_status === 'RECOMMEND_FOR_APPROVAL' ? 'var(--color-amber-border)' : 'var(--color-emerald-border)';
  const StatusIcon = dec?.decision_status === 'BLOCK' ? Ban : dec?.decision_status === 'RECOMMEND_FOR_APPROVAL' ? UserCheck : CheckCircle2;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(8, 11, 18, 0.8)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, padding: 'var(--space-6)',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-primary)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-xl)',
          width: '100%', maxWidth: '960px', maxHeight: '90vh',
          overflowY: 'auto',
          color: 'var(--text-primary)',
          boxShadow: 'var(--shadow-xl)',
        }}
      >
        {/* ── Modal Header ── */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: 'var(--space-5) var(--space-6)',
          borderBottom: '1px solid var(--border-subtle)',
          position: 'sticky', top: 0,
          background: 'var(--bg-primary)',
          zIndex: 1,
          borderRadius: 'var(--radius-xl) var(--radius-xl) 0 0',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 700 }}>Decision Studio</h2>
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{payment.payment_id}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: '2px' }}>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{payment.customer_name}</span>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)' }}>·</span>
              <span className="badge badge-neutral">{payment.payment_method}</span>
              <span className="badge badge-rose">{payment.failure_reason}</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <button onClick={handleEvaluate} disabled={isEvaluating} className="btn-secondary" style={{ fontSize: 'var(--text-xs)', padding: '6px 12px' }}>
              <Cpu size={13} />
              {isEvaluating ? 'Scoring...' : 'Re-Evaluate'}
            </button>
            <button onClick={onClose} className="btn-ghost" style={{ padding: '6px' }}>
              <X size={18} />
            </button>
          </div>
        </div>

        <div style={{ padding: 'var(--space-6)' }}>

          {/* ── AI Decision Hero ── */}
          {dec && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto',
              gap: 'var(--space-5)',
              marginBottom: 'var(--space-5)',
              padding: 'var(--space-5)',
              background: statusBg,
              border: `1px solid ${statusBorder}`,
              borderRadius: 'var(--radius-lg)',
            }}>
              <div>
                <div className="label" style={{ color: statusColor, marginBottom: 'var(--space-2)' }}>
                  AI Decision
                </div>
                <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
                  {dec.selected_action}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                  <span className={`badge ${dec.decision_status === 'BLOCK' ? 'badge-rose' : dec.decision_status === 'RECOMMEND_FOR_APPROVAL' ? 'badge-amber' : 'badge-emerald'}`}>
                    <StatusIcon size={11} />
                    {dec.decision_status.replace(/_/g, ' ')}
                  </span>
                  <span className="badge badge-neutral">{dec.execution_status.replace(/_/g, ' ')}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-6)', alignItems: 'flex-start' }}>
                <div style={{ textAlign: 'right' }}>
                  <div className="label" style={{ marginBottom: '2px' }}>P(Recovery)</div>
                  <div className="metric-lg" style={{ color: dec.predicted_recovery_probability >= 0.5 ? 'var(--color-emerald)' : 'var(--color-amber)' }}>
                    {(dec.predicted_recovery_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="label" style={{ marginBottom: '2px' }}>Expected Net Value</div>
                  <div className="metric-lg" style={{ color: dec.expected_net_value > 0 ? 'var(--color-emerald)' : 'var(--color-rose)' }}>
                    ₹{dec.expected_net_value.toLocaleString('en-IN')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="label" style={{ marginBottom: '2px' }}>Amount</div>
                  <div className="metric-lg" style={{ color: 'var(--text-primary)' }}>
                    ₹{payment.amount.toLocaleString('en-IN')}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Why RecoverIQ Chose This ── */}
          {dec && (
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                <Sparkles size={15} style={{ color: 'var(--color-violet)' }} />
                <h3 className="section-title">Why RecoverIQ Chose This</h3>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="responsive-grid-2">
                {/* Why Selected */}
                <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid var(--color-emerald)' }}>
                  <div className="label" style={{ color: 'var(--color-emerald)', marginBottom: 'var(--space-2)' }}>Why Selected</div>
                  <p style={{ fontSize: 'var(--text-base)', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {dec.explanation.why_selected}
                  </p>
                </div>

                {/* Why Not Alternatives */}
                <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid var(--color-amber)' }}>
                  <div className="label" style={{ color: 'var(--color-amber)', marginBottom: 'var(--space-2)' }}>Why Not Alternatives</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                    {Object.entries(dec.explanation.why_not_selected).slice(0, 3).map(([a, r]) => (
                      <div key={a} style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{a}:</span> {r}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Decision Flow Pipeline ── */}
          {dec && (
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <h3 className="section-title" style={{ marginBottom: 'var(--space-3)' }}>Decision Pipeline</h3>
              <div className="card" style={{ padding: 'var(--space-4) var(--space-5)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' }}>
                  {[
                    { label: 'Failed Payment', detail: `₹${payment.amount.toLocaleString('en-IN')} · ${payment.failure_reason}`, color: 'var(--color-rose)' },
                    { label: 'Context Analysis', detail: `${payment.payment_method} · ${payment.customer_name}`, color: 'var(--color-blue)' },
                    { label: 'Recovery Model', detail: `P = ${(dec.predicted_recovery_probability * 100).toFixed(1)}%`, color: 'var(--color-violet)' },
                    { label: `${dec.feasible_actions.length} Feasible Actions`, detail: `of ${dec.candidate_actions.length} candidates`, color: 'var(--color-blue)' },
                    { label: 'ENV Optimization', detail: `Best: ₹${dec.expected_net_value.toLocaleString('en-IN')}`, color: 'var(--color-emerald)' },
                    { label: `${dec.guardrail_results.length} Guardrails`, detail: dec.guardrail_results.some(g => g.status === 'BLOCK') ? 'Constraint active' : 'All passed', color: dec.guardrail_results.some(g => g.status === 'BLOCK') ? 'var(--color-rose)' : 'var(--color-emerald)' },
                    { label: dec.selected_action, detail: dec.decision_status.replace(/_/g, ' '), color: statusColor },
                  ].map((step, idx, arr) => (
                    <React.Fragment key={idx}>
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                        padding: 'var(--space-2) var(--space-3)',
                        minWidth: '0',
                        flex: '1 1 auto',
                      }}>
                        <div style={{
                          width: '8px', height: '8px', borderRadius: '50%',
                          background: step.color, marginBottom: '4px', flexShrink: 0,
                        }} />
                        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', textAlign: 'center', lineHeight: '1.3' }}>
                          {step.label}
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center', lineHeight: '1.3', marginTop: '1px' }}>
                          {step.detail}
                        </div>
                      </div>
                      {idx < arr.length - 1 && (
                        <ArrowRight size={12} style={{ color: 'var(--text-faint)', flexShrink: 0 }} />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── Guardrail Results ── */}
          {dec && dec.guardrail_results.length > 0 && (
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                <ShieldCheck size={15} style={{ color: 'var(--color-amber)' }} />
                <h3 className="section-title">Safety Guardrails</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {dec.guardrail_results.map((g, idx) => (
                  <div key={idx} className="card" style={{
                    padding: 'var(--space-3) var(--space-4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    borderLeft: `3px solid ${g.status === 'BLOCK' ? 'var(--color-rose)' : g.status === 'ESCALATE' ? 'var(--color-amber)' : 'var(--color-emerald)'}`,
                  }}>
                    <div>
                      <div style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)' }}>{g.guardrail}</div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '1px' }}>{g.reason}</div>
                    </div>
                    <span className={`badge ${g.status === 'BLOCK' ? 'badge-rose' : g.status === 'ESCALATE' ? 'badge-amber' : 'badge-emerald'}`}>
                      {g.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Candidate Action Evaluation Matrix ── */}
          {dec && (
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <h3 className="section-title" style={{ marginBottom: 'var(--space-3)' }}>Candidate Action Evaluation Matrix</h3>
              <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Candidate Action</th>
                      <th>P(Recovery)</th>
                      <th>Intervention Cost</th>
                      <th>Incentive Cost</th>
                      <th>Fatigue Penalty</th>
                      <th>Expected Net Value</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dec.candidate_actions.map((act) => {
                      const isWinning = act === dec.selected_action;
                      const score = getScoreForAction(act);
                      const isFeasible = dec.feasible_actions.includes(act);

                      return (
                        <tr
                          key={act}
                          style={{
                            background: isWinning ? 'var(--color-emerald-bg)' : undefined,
                          }}
                        >
                          <td style={{ fontWeight: isWinning ? 700 : 500 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                              {isWinning && <span style={{ width: '3px', height: '16px', borderRadius: '2px', background: 'var(--color-emerald)', display: 'inline-block' }} />}
                              <span style={{ color: isWinning ? 'var(--color-emerald)' : 'var(--text-primary)' }}>{act}</span>
                              {isWinning && <span className="badge badge-emerald" style={{ fontSize: '9px', padding: '1px 5px' }}>SELECTED</span>}
                            </div>
                          </td>
                          <td style={{
                            fontWeight: 600,
                            color: score && !score.is_blocked
                              ? (score.predicted_p_recovery >= 0.5 ? 'var(--color-emerald)' : 'var(--color-amber)')
                              : 'var(--text-faint)',
                          }}>
                            {score ? `${(score.predicted_p_recovery * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td style={{ color: score?.is_blocked ? 'var(--text-faint)' : 'var(--text-secondary)' }}>
                            ₹{score ? score.intervention_cost.toFixed(2) : '—'}
                          </td>
                          <td style={{ color: score?.is_blocked ? 'var(--text-faint)' : 'var(--text-secondary)' }}>
                            ₹{score ? score.incentive_cost.toFixed(2) : '—'}
                          </td>
                          <td style={{ color: score?.is_blocked ? 'var(--text-faint)' : (score && score.fatigue_penalty > 0 ? 'var(--color-amber)' : 'var(--text-secondary)') }}>
                            ₹{score ? score.fatigue_penalty.toFixed(2) : '—'}
                          </td>
                          <td style={{
                            fontWeight: 700,
                            color: isWinning ? 'var(--color-emerald)' : (score && !score.is_blocked && score.expected_net_value > 0 ? 'var(--text-secondary)' : 'var(--color-rose)'),
                          }}>
                            {score ? `₹${score.expected_net_value.toLocaleString('en-IN')}` : '—'}
                          </td>
                          <td>
                            {score?.is_blocked ? (
                              <span style={{ color: 'var(--color-rose)', fontSize: 'var(--text-xs)' }}>
                                {score.block_reason || 'Blocked'}
                              </span>
                            ) : isFeasible ? (
                              <span style={{ color: 'var(--color-emerald)', fontSize: 'var(--text-xs)', fontWeight: 600 }}>Feasible</span>
                            ) : (
                              <span style={{ color: 'var(--text-faint)', fontSize: 'var(--text-xs)' }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Local Feature Attributions (SHAP Waterfall) ── */}
          {attributions && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-4)',
              marginBottom: 'var(--space-5)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Sparkles size={16} color="var(--color-blue)" />
                  <h3 className="section-title">Local Feature Attribution (SHAP Marginal Shift)</h3>
                </div>
                <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  Base P: 42.0% → Net Lift: {attributions.net_lift_from_base >= 0 ? '+' : ''}{(attributions.net_lift_from_base * 100).toFixed(1)} pp
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {attributions.attributions.map((attr, idx) => (
                  <div key={idx} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 60px', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {attr.label}
                    </span>
                    <div style={{ position: 'relative', height: '10px', background: 'var(--bg-inset)', borderRadius: '5px', overflow: 'hidden' }}>
                      {attr.direction === 'positive' ? (
                        <div
                          style={{
                            position: 'absolute',
                            left: '50%',
                            width: `${Math.min(50, Math.abs(attr.contribution) * 150)}%`,
                            height: '100%',
                            background: 'var(--color-emerald)',
                            borderRadius: '0 5px 5px 0'
                          }}
                        />
                      ) : (
                        <div
                          style={{
                            position: 'absolute',
                            right: '50%',
                            width: `${Math.min(50, Math.abs(attr.contribution) * 150)}%`,
                            height: '100%',
                            background: 'var(--color-rose)',
                            borderRadius: '5px 0 0 5px'
                          }}
                        />
                      )}
                      <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '2px', background: 'var(--border-strong)' }} />
                    </div>
                    <span style={{
                      fontSize: 'var(--text-xs)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      textAlign: 'right',
                      color: attr.direction === 'positive' ? 'var(--color-emerald)' : 'var(--color-rose)'
                    }}>
                      {attr.contribution >= 0 ? '+' : ''}{(attr.contribution * 100).toFixed(1)} pp
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Customer Message Preview ── */}
          {dec?.explanation?.customer_message_preview && (
            <div style={{
              background: 'var(--color-violet-bg)',
              border: '1px solid var(--color-violet-border)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-4)',
              marginBottom: 'var(--space-5)',
            }}>
              <div className="label" style={{ color: 'var(--color-violet)', marginBottom: 'var(--space-2)' }}>
                Personalized Communication Preview
              </div>
              <p style={{ fontSize: 'var(--text-base)', color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: '1.6' }}>
                "{dec.explanation.customer_message_preview}"
              </p>
            </div>
          )}

          {/* ── Execution Controls ── */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: 'var(--space-4)',
          }}>
            <div>
              {execMessage && (
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--color-emerald)' }}>
                  {execMessage}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              {dec?.decision_status === 'RECOMMEND_FOR_APPROVAL' && dec.execution_status !== 'APPROVED' && (
                <>
                  <button onClick={handleReject} className="btn-secondary" style={{ borderColor: 'var(--color-rose)', color: 'var(--color-rose)', fontSize: 'var(--text-sm)' }}>
                    <XCircle size={14} /> Reject
                  </button>
                  <button onClick={handleApprove} className="btn-primary" style={{ background: 'var(--color-amber)', fontSize: 'var(--text-sm)' }}>
                    <UserCheck size={14} /> Approve Decision
                  </button>
                </>
              )}
              <button
                onClick={handleExecute}
                disabled={isExecuting || dec?.decision_status === 'BLOCK' || dec?.execution_status === 'REJECTED'}
                className="btn-primary"
                style={{
                  background: dec?.decision_status === 'BLOCK' || dec?.execution_status === 'REJECTED' ? 'var(--text-faint)' : undefined,
                  fontSize: 'var(--text-sm)',
                }}
              >
                <Play size={14} />
                {isExecuting ? 'Simulating...' : (dec?.decision_status === 'BLOCK' ? 'Blocked' : dec?.execution_status === 'REJECTED' ? 'Rejected' : 'Execute Simulation')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

