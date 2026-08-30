import React, { useState, useEffect } from 'react';
import {
  Play,
  CheckCircle2,
  Copy,
  Check,
  Clock,
  ExternalLink,
  ArrowRight,
  Terminal
} from 'lucide-react';

import { getSampleWebhooks, sendRazorpayWebhook } from '../services/api';
import type { RazorpayWebhookReceipt } from '../types';

export const RazorpayWebhookHub: React.FC = () => {
  const [samples, setSamples] = useState<Record<string, any>>({});
  const [selectedKey, setSelectedKey] = useState<string>('payment.failed.insufficient_funds');
  const [jsonText, setJsonText] = useState<string>('');
  const [receipt, setReceipt] = useState<RazorpayWebhookReceipt | null>(null);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);
  const [copiedPayload, setCopiedPayload] = useState<boolean>(false);
  const [activeEditorTab, setActiveEditorTab] = useState<'editor' | 'curl' | 'preview'>('preview');
  const [history, setHistory] = useState<RazorpayWebhookReceipt[]>([]);

  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const res = await getSampleWebhooks();
        setSamples(res);
        if (res['payment.failed.insufficient_funds']) {
          setJsonText(JSON.stringify(res['payment.failed.insufficient_funds'], null, 2));
        }
      } catch (err) {
        console.error('Error fetching sample webhooks:', err);
      }
    };
    fetchSamples();
  }, []);

  const handleSelectPreset = (key: string) => {
    setSelectedKey(key);
    if (samples[key]) {
      setJsonText(JSON.stringify(samples[key], null, 2));
    }
  };

  const handleSendWebhook = async () => {
    setIsIngesting(true);
    try {
      const parsed = JSON.parse(jsonText);
      const res = await sendRazorpayWebhook(parsed);
      setReceipt(res);
      setHistory((prev) => [res, ...prev.slice(0, 4)]);
    } catch (err: any) {
      alert(`Invalid JSON or Error: ${err.message || 'Server error'}`);
    } finally {
      setIsIngesting(false);
    }
  };

  const copyPaymentLink = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const copyPayload = () => {
    navigator.clipboard.writeText(jsonText);
    setCopiedPayload(true);
    setTimeout(() => setCopiedPayload(false), 2000);
  };

  const copyCurl = () => {
    const curlCmd = `curl -X POST http://localhost:8000/api/webhooks/razorpay \\\n  -H "Content-Type: application/json" \\\n  -d '${jsonText.replace(/\n/g, '')}'`;
    navigator.clipboard.writeText(curlCmd);
    setCopiedPayload(true);
    setTimeout(() => setCopiedPayload(false), 2000);
  };

  // High-performance JSON Syntax Highlighter
  const renderHighlightedJSON = (jsonStr: string) => {
    try {
      const parsed = JSON.parse(jsonStr);
      const formatted = JSON.stringify(parsed, null, 2);
      const lines = formatted.split('\n');

      return (
        <div style={{ display: 'flex', fontSize: '12px', lineHeight: '1.6', fontFamily: 'var(--font-mono)' }}>
          {/* Line Numbers Gutter */}
          <div style={{
            paddingRight: '16px',
            marginRight: '16px',
            borderRight: '1px solid var(--border-subtle)',
            color: 'var(--text-faint)',
            userSelect: 'none',
            textAlign: 'right',
            minWidth: '28px'
          }}>
            {lines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          {/* Formatted Code */}
          <div style={{ flex: 1, overflowX: 'auto' }}>
            {lines.map((line, i) => {
              // Regex highlight keys, strings, numbers, booleans
              const keyMatch = line.match(/^(\s*)(".*?")(\s*:\s*)(.*)$/);
              if (keyMatch) {
                const [, indent, key, colon, value] = keyMatch;
                let valColor = 'var(--text-primary)';
                if (value.startsWith('"')) valColor = '#34d399'; // string green
                else if (/^\d/.test(value) || /^-?\d/.test(value)) valColor = '#fbbf24'; // number amber
                else if (/true|false/.test(value)) valColor = '#f472b6'; // bool pink
                else if (/null/.test(value)) valColor = '#94a3b8'; // null

                return (
                  <div key={i}>
                    <span>{indent}</span>
                    <span style={{ color: '#93c5fd', fontWeight: 600 }}>{key}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{colon}</span>
                    <span style={{ color: valColor }}>{value}</span>
                  </div>
                );
              }

              return (
                <div key={i} style={{ color: 'var(--text-secondary)' }}>
                  {line}
                </div>
              );
            })}
          </div>
        </div>
      );
    } catch {
      return <pre style={{ color: 'var(--color-danger-text)' }}>{jsonStr}</pre>;
    }
  };

  const presets = [
    { key: 'payment.failed.insufficient_funds', label: 'Insufficient Funds', sub: 'Debit · ₹3,500', tag: 'Retry Delay 18h' },
    { key: 'payment.failed.expired_card', label: 'Expired Card', sub: 'Credit · ₹12,500', tag: 'Method Update' },
    { key: 'payment.failed.high_value_auth', label: 'High-Value Auth', sub: 'NetBanking · ₹85,000', tag: 'Approval Escalation' },
    { key: 'payment.failed.dnc_customer', label: 'DNC Opt-Out', sub: 'UPI · ₹1,800', tag: 'Hard Block' },
    { key: 'subscription.halted.recurring_card', label: 'Subscription Halt', sub: 'AutoPay · ₹4,999', tag: 'Smart Dunning' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header */}
      <div>
        <h2 className="page-title">Webhook Gateway & Execution Studio</h2>
        <p className="section-subtitle" style={{ marginTop: '2px' }}>
          Simulate incoming Razorpay webhook events, inspect payload extraction, and observe live autonomous decisioning.
        </p>
      </div>

      {/* Scenario Presets Bar */}
      <div className="card" style={{ padding: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <span className="label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Terminal size={13} color="var(--color-interactive-text)" />
            Select Failure Scenario
          </span>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Click to load standardized gateway event</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '8px' }}>
          {presets.map((item) => {
            const isSelected = selectedKey === item.key;
            return (
              <button
                key={item.key}
                onClick={() => handleSelectPreset(item.key)}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: isSelected ? '1px solid var(--border-focus)' : '1px solid var(--border-default)',
                  background: isSelected ? 'var(--bg-hover)' : 'var(--bg-inset)',
                  color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontSize: 'var(--text-sm)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                <div style={{ fontWeight: isSelected ? 700 : 600, color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>{item.sub}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-success-text)', marginTop: '4px', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                  → {item.tag}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Code Terminal on Left, Decision Card on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: 'var(--space-5)' }} className="responsive-grid-2">
        {/* Code Terminal */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', background: '#09090b', border: '1px solid var(--border-default)' }}>
          {/* Terminal Window Top Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            background: 'var(--bg-card)',
            borderBottom: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', opacity: 0.8 }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', opacity: 0.8 }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', opacity: 0.8 }} />
              </div>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginLeft: '6px' }}>
                POST /api/webhooks/razorpay
              </span>
            </div>

            {/* Mode Switcher Tabs */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={() => setActiveEditorTab('preview')}
                style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  background: activeEditorTab === 'preview' ? 'var(--bg-hover)' : 'transparent',
                  color: activeEditorTab === 'preview' ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: activeEditorTab === 'preview' ? 600 : 400
                }}
              >
                Highlighted
              </button>
              <button
                onClick={() => setActiveEditorTab('editor')}
                style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  background: activeEditorTab === 'editor' ? 'var(--bg-hover)' : 'transparent',
                  color: activeEditorTab === 'editor' ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: activeEditorTab === 'editor' ? 600 : 400
                }}
              >
                Raw Editor
              </button>
              <button
                onClick={() => setActiveEditorTab('curl')}
                style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  background: activeEditorTab === 'curl' ? 'var(--bg-hover)' : 'transparent',
                  color: activeEditorTab === 'curl' ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: activeEditorTab === 'curl' ? 600 : 400
                }}
              >
                cURL
              </button>
              <button
                onClick={activeEditorTab === 'curl' ? copyCurl : copyPayload}
                style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-default)',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginLeft: '4px'
                }}
              >
                {copiedPayload ? <Check size={10} color="var(--color-success-text)" /> : <Copy size={10} />}
                {copiedPayload ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Terminal Body */}
          <div style={{ flex: 1, minHeight: '340px', maxHeight: '420px', overflowY: 'auto', padding: '14px', background: '#09090b' }}>
            {activeEditorTab === 'preview' && renderHighlightedJSON(jsonText)}

            {activeEditorTab === 'editor' && (
              <textarea
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                style={{
                  width: '100%',
                  height: '320px',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: '#34d399',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  lineHeight: '1.6',
                  resize: 'none'
                }}
              />
            )}

            {activeEditorTab === 'curl' && (
              <pre style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                color: '#60a5fa',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                margin: 0
              }}>
{`curl -X POST http://localhost:8000/api/webhooks/razorpay \\
  -H "Content-Type: application/json" \\
  -d '${jsonText}'`}
              </pre>
            )}
          </div>

          {/* Terminal Action Footer */}
          <div style={{
            padding: '10px 14px',
            background: 'var(--bg-card)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Format: <strong style={{ color: 'var(--text-secondary)' }}>Razorpay Webhook Payload v1</strong>
            </span>
            <button
              onClick={handleSendWebhook}
              disabled={isIngesting}
              className="btn-primary"
              style={{
                padding: '7px 16px',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Play size={13} />
              {isIngesting ? 'Executing Model...' : 'Dispatch Webhook & Decide'}
            </button>
          </div>
        </div>

        {/* Right Side: Live Autonomous Decision Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {receipt ? (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 'var(--space-3)', borderBottom: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={18} style={{ color: 'var(--color-success-text)' }} />
                  <div>
                    <h4 style={{ fontSize: 'var(--text-md)', fontWeight: 700 }}>Decision Dispatched</h4>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Event: {receipt.webhook_event}</span>
                  </div>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)',
                  color: 'var(--color-success-text)', fontWeight: 600,
                  background: 'var(--color-success-bg)', padding: '3px 8px', borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(16, 185, 129, 0.2)'
                }}>
                  <Clock size={12} /> {receipt.execution_latency_ms.toFixed(1)} ms
                </div>
              </div>

              {/* Grid Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: 'var(--text-sm)' }}>
                {[
                  { label: 'Payment ID', value: receipt.payment_id, mono: true },
                  { label: 'Failed Amount', value: `₹${receipt.amount_inr.toLocaleString('en-IN')}`, mono: true },
                  { label: 'Optimal Action', value: receipt.selected_action, color: 'var(--color-interactive-text)', bold: true },
                  { label: 'Calibrated P(Recovery)', value: `${(receipt.predicted_recovery_probability * 100).toFixed(1)}%`, color: 'var(--color-success-text)', mono: true, bold: true },
                  { label: 'Expected Net Value (ENV)', value: `₹${receipt.expected_net_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, color: receipt.expected_net_value > 0 ? 'var(--color-success-text)' : 'var(--text-muted)', mono: true, bold: true },
                  { label: 'Decision Status', value: receipt.decision_status, color: receipt.decision_status === 'BLOCK' ? 'var(--color-danger-text)' : receipt.decision_status === 'RECOMMEND_FOR_APPROVAL' ? 'var(--color-warning-text)' : 'var(--color-success-text)', bold: true },
                ].map((d, i) => (
                  <div key={i} style={{ padding: '8px 10px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: 'var(--text-xs)' }}>{d.label}</span>
                    <span style={{ fontWeight: d.bold ? 700 : 500, fontFamily: d.mono ? 'var(--font-mono)' : undefined, color: d.color || 'var(--text-primary)' }}>
                      {d.value}
                    </span>
                  </div>
                ))}
              </div>

              {/* Payment Link (if generated) */}
              {receipt.razorpay_payment_link && (
                <div style={{ padding: '10px 12px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-interactive-text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ExternalLink size={12} /> Razorpay Payment Link Generated
                    </span>
                    <button onClick={() => copyPaymentLink(receipt.razorpay_payment_link!)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '2px 8px', background: 'transparent', border: '1px solid var(--border-default)',
                        borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)',
                        fontSize: 'var(--text-xs)', cursor: 'pointer'
                      }}>
                      {copiedLink ? <Check size={11} color="var(--color-success-text)" /> : <Copy size={11} />}
                      {copiedLink ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <div style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                    {receipt.razorpay_payment_link}
                  </div>
                </div>
              )}

              {/* Rationale */}
              <div style={{ padding: '10px 12px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '3px' }}>Autonomous Rationale:</span>
                {receipt.explanation}
              </div>
            </div>
          ) : (
            <div className="card" style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              textAlign: 'center', minHeight: '360px', padding: 'var(--space-8)'
            }}>
              <h4 style={{ fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: '6px' }}>
                Awaiting Webhook Trigger
              </h4>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', maxWidth: '300px', lineHeight: 1.45 }}>
                Select a preset scenario on the left or customize the JSON payload, then click Dispatch Webhook to observe the autonomous decision.
              </p>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px', marginTop: 'var(--space-4)',
                fontSize: 'var(--text-xs)', color: 'var(--text-muted)'
              }}>
                <span>Payload Ingest</span>
                <ArrowRight size={10} />
                <span>Platt Calibration</span>
                <ArrowRight size={10} />
                <span style={{ color: 'var(--color-success-text)', fontWeight: 600 }}>ENV Maximization</span>
              </div>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <span className="label" style={{ marginBottom: '6px', display: 'block' }}>Recent Ingested Webhooks</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {history.map((h, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '8px 12px', background: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--text-xs)', border: '1px solid var(--border-subtle)'
                  }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{h.payment_id}</span>
                    <span style={{ color: 'var(--color-interactive-text)', fontWeight: 500 }}>{h.selected_action}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-success-text)', fontWeight: 700 }}>₹{h.amount_inr.toLocaleString('en-IN')}</span>
                    <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{h.execution_latency_ms.toFixed(1)}ms</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
