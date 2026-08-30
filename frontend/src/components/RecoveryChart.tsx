import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface RecoveryChartProps {
  data: any[];
}

export const RecoveryChart: React.FC<RecoveryChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  const lastPoint = data[data.length - 1];
  const delta = lastPoint ? (lastPoint.RecoverIQ || 0) - (lastPoint.Baseline || 0) : 0;

  return (
    <div className="card" style={{ marginBottom: 'var(--space-6)', padding: 'var(--space-5)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <div>
          <h3 className="section-title">Recovery Performance</h3>
          <p className="section-subtitle" style={{ marginTop: '2px' }}>14-day cohort — Baseline vs RecoverIQ</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-5)', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '2px', background: 'var(--text-faint)', display: 'inline-block' }} />
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Baseline</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '2px', background: 'var(--color-success)', display: 'inline-block' }} />
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-success-text)' }}>RecoverIQ</span>
          </div>
          {delta > 0 && (
            <span className="badge badge-green">
              +₹{(delta / 1000).toFixed(1)}k
            </span>
          )}
        </div>
      </div>

      {/* Chart */}
      <div style={{ height: '260px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRecoverIQ" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.12}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
              </linearGradient>
              <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#52525b" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#52525b" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
            <XAxis
              dataKey="day"
              stroke="var(--text-faint)"
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              axisLine={{ stroke: 'var(--border-subtle)' }}
              tickLine={false}
            />
            <YAxis
              stroke="var(--text-faint)"
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              tickFormatter={(val) => `₹${(val/1000).toFixed(0)}k`}
              axisLine={false}
              tickLine={false}
              width={55}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-sm)',
                padding: '8px 12px',
                boxShadow: 'var(--shadow-md)',
              }}
              formatter={(value: any, name: any) => [
                `₹${Number(value).toLocaleString('en-IN')}`,
                String(name || '')
              ]}
              labelStyle={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', marginBottom: '4px' }}
            />
            <Area
              type="monotone"
              dataKey="Baseline"
              stroke="var(--text-faint)"
              strokeWidth={1.5}
              fillOpacity={1}
              fill="url(#colorBaseline)"
              dot={false}
            />
            <Area
              type="monotone"
              dataKey="RecoverIQ"
              stroke="var(--color-success)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRecoverIQ)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
