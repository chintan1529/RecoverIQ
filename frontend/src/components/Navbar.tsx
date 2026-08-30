import React from 'react';
import { BarChart3, Layers, Sliders, Webhook, Cpu, Calculator, FlaskConical, Activity } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: BarChart3 },
    { id: 'queue', label: 'Queue', icon: Layers },
    { id: 'what-if', label: 'What-If', icon: Sliders },
    { id: 'razorpay-hub', label: 'Webhooks', icon: Webhook },
    { id: 'model-science', label: 'Model', icon: Cpu },
    { id: 'roi-calculator', label: 'ROI', icon: Calculator },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical },
    { id: 'agent', label: 'Audit', icon: Activity },
  ];

  return (
    <header style={{
      background: 'var(--bg-primary)',
      borderBottom: '1px solid var(--border-default)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '0 var(--space-6)',
        height: '52px',
        gap: 'var(--space-8)'
      }}>
        {/* Logo */}
        <span style={{
          fontSize: '15px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          letterSpacing: '-0.03em',
          flexShrink: 0,
          cursor: 'pointer',
        }}
          onClick={() => setActiveTab('dashboard')}
        >
          RecoverIQ
        </span>

        {/* Navigation tabs */}
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
          flex: 1,
        }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  background: isActive ? 'var(--bg-hover)' : 'transparent',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'color var(--transition-fast)',
                  fontFamily: 'var(--font-sans)',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.color = 'var(--text-secondary)';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.color = 'var(--text-muted)';
                }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Status dot */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          flexShrink: 0,
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: 'var(--color-success)',
          }} />
          <span>Connected</span>
        </div>
      </div>
    </header>
  );
};
