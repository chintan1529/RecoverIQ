import React, { useEffect, useState, lazy, Suspense } from 'react';
import { Navbar } from './components/Navbar';
import { KPIOverview } from './components/KPIOverview';
import { PaymentQueue } from './components/PaymentQueue';

// Lazy load secondary and heavyweight tab views for optimal bundle splitting
const RecoveryChart = lazy(() => import('./components/RecoveryChart').then(m => ({ default: m.RecoveryChart })));
const PaymentDetailStudio = lazy(() => import('./components/PaymentDetailStudio').then(m => ({ default: m.PaymentDetailStudio })));
const StrategyIntelligence = lazy(() => import('./components/StrategyIntelligence').then(m => ({ default: m.StrategyIntelligence })));
const ExperimentStudio = lazy(() => import('./components/ExperimentStudio').then(m => ({ default: m.ExperimentStudio })));
const AgentAuditFeed = lazy(() => import('./components/AgentAuditFeed').then(m => ({ default: m.AgentAuditFeed })));
const WhatIfSimulator = lazy(() => import('./components/WhatIfSimulator').then(m => ({ default: m.WhatIfSimulator })));
const RazorpayWebhookHub = lazy(() => import('./components/RazorpayWebhookHub').then(m => ({ default: m.RazorpayWebhookHub })));
const ModelScienceInspector = lazy(() => import('./components/ModelScienceInspector').then(m => ({ default: m.ModelScienceInspector })));
const EnterpriseRoiCalculator = lazy(() => import('./components/EnterpriseRoiCalculator').then(m => ({ default: m.EnterpriseRoiCalculator })));

import {
  getAnalyticsSummary,
  getRecoveryChartData,
  getPayments,
  seedDemoEnvironment
} from './services/api';
import type { AnalyticsSummary, Payment } from './types';

const TabFallback: React.FC = () => (
  <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)' }}>
    Loading module chunk...
  </div>
);

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [sumRes, chartRes, payRes] = await Promise.all([
        getAnalyticsSummary(),
        getRecoveryChartData(),
        getPayments()
      ]);
      setSummary(sumRes);
      setChartData(chartRes);
      setPayments(payRes);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSeedData = async () => {
    setIsSeeding(true);
    try {
      await seedDemoEnvironment();
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-root)', color: 'var(--text-primary)' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: 'var(--space-6)' }}>
        <Suspense fallback={<TabFallback />}>
          {activeTab === 'dashboard' && (
            <div className="animate-in">
              <KPIOverview summary={summary} onSeedData={handleSeedData} isSeeding={isSeeding} />
              <RecoveryChart data={chartData} />
              <PaymentQueue payments={payments} onSelectPayment={setSelectedPayment} />
            </div>
          )}

          {activeTab === 'queue' && (
            <div className="animate-in">
              <PaymentQueue payments={payments} onSelectPayment={setSelectedPayment} />
            </div>
          )}

          {activeTab === 'what-if' && (
            <div className="animate-in">
              <WhatIfSimulator />
            </div>
          )}

          {activeTab === 'razorpay-hub' && (
            <div className="animate-in">
              <RazorpayWebhookHub />
            </div>
          )}

          {activeTab === 'model-science' && (
            <div className="animate-in">
              <ModelScienceInspector />
            </div>
          )}

          {activeTab === 'roi-calculator' && (
            <div className="animate-in">
              <EnterpriseRoiCalculator />
            </div>
          )}

          {activeTab === 'strategies' && (
            <div className="animate-in">
              <StrategyIntelligence />
            </div>
          )}

          {activeTab === 'experiments' && (
            <div className="animate-in">
              <ExperimentStudio />
            </div>
          )}

          {activeTab === 'agent' && (
            <div className="animate-in">
              <AgentAuditFeed />
            </div>
          )}
        </Suspense>
      </main>

      {/* Decision Studio Modal */}
      {selectedPayment && (
        <Suspense fallback={<TabFallback />}>
          <PaymentDetailStudio
            payment={selectedPayment}
            onClose={() => setSelectedPayment(null)}
            onRefresh={loadData}
          />
        </Suspense>
      )}
    </div>
  );
};

export default App;
