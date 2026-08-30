import axios from 'axios';
import type {
  Payment,
  DecisionContract,
  AnalyticsSummary,
  ExperimentResponse,
  AgentEvent,
  StrategyPerformance
} from '../types';

const API_BASE = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': (import.meta as any).env?.VITE_OPERATOR_API_KEY || 'test_operator_key',
  },
});

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const getAnalyticsSummary = async (): Promise<AnalyticsSummary> => {
  const res = await api.get('/analytics/summary');
  return res.data;
};

export const getRecoveryChartData = async () => {
  const res = await api.get('/analytics/recovery-chart');
  return res.data;
};

export const getPayments = async (status?: string, failure_reason?: string): Promise<Payment[]> => {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  if (failure_reason) params.failure_reason = failure_reason;
  const res = await api.get('/payments', { params });
  return res.data;
};

export const getPaymentDetail = async (paymentId: string): Promise<Payment> => {
  const res = await api.get(`/payments/${paymentId}`);
  return res.data;
};

export const evaluatePayment = async (paymentId: string): Promise<DecisionContract> => {
  const res = await api.post(`/payments/${paymentId}/evaluate`);
  return res.data;
};

export const executePaymentSimulation = async (paymentId: string) => {
  const res = await api.post(`/payments/${paymentId}/execute`);
  return res.data;
};

export const approvePaymentDecision = async (paymentId: string) => {
  const res = await api.post(`/payments/${paymentId}/approve`);
  return res.data;
};

export const runExperiment = async (sampleSize: number = 2000, seed: number = 42): Promise<ExperimentResponse> => {
  const res = await api.post('/experiments/run', {
    sample_size: sampleSize,
    random_seed: seed,
    baseline_policy_name: 'Standard Retry Schedule',
    ai_policy_name: 'RecoverIQ Decision Engine'
  });
  return res.data;
};

export const getStrategyPerformance = async (): Promise<StrategyPerformance[]> => {
  const res = await api.get('/strategies');
  return res.data;
};

export const getAgentActivity = async (): Promise<AgentEvent[]> => {
  const res = await api.get('/agent/activity');
  return res.data;
};

export const seedDemoEnvironment = async () => {
  const res = await api.post('/demo/seed');
  return res.data;
};

export const simulateWhatIf = async (features: any) => {
  const res = await api.post('/payments/what-if', features);
  return res.data;
};

export const getPaymentAttributions = async (paymentId: string) => {
  const res = await api.get(`/payments/${paymentId}/attributions`);
  return res.data;
};

export const getSampleWebhooks = async () => {
  const res = await api.get('/webhooks/samples');
  return res.data;
};

export const sendRazorpayWebhook = async (payload: any) => {
  const res = await api.post('/webhooks/razorpay', payload);
  return res.data;
};

export const getModelCalibrationData = async () => {
  const res = await api.get('/analytics/calibration');
  return res.data;
};

export const calculateEnterpriseRoi = async (params: {
  monthly_gmv?: number;
  failure_rate_pct?: number;
  aov?: number;
  margin_pct?: number;
}) => {
  const res = await api.get('/analytics/roi-calculator', { params });
  return res.data;
};

export const rejectPaymentDecision = async (paymentId: string) => {
  const res = await api.post(`/payments/${paymentId}/reject`);
  return res.data;
};

