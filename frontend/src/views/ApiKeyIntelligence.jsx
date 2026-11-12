import React, { useState, useEffect } from 'react';
import { 
  Key, 
  Play, 
  BarChart2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Database, 
  Layers, 
  ShieldCheck, 
  RefreshCw, 
  Copy, 
  Check, 
  Search, 
  Filter, 
  Sparkles,
  Info,
  ExternalLink,
  Cpu,
  ArrowRight,
  Clock,
  ChevronRight,
  CheckCircle,
  Hash
} from 'lucide-react';

const BASE_URL = import.meta.env.VITE_API_URL !== undefined
  ? import.meta.env.VITE_API_URL
  : (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');
const API_BASE = `${BASE_URL.replace(/\/+$/, '')}/api/dataset`;

const PROVIDER_OPTIONS = [
  { value: '', label: 'Any / All Providers' },
  { value: 'aws', label: 'AWS (Amazon Web Services)' },
  { value: 'openai', label: 'OpenAI (sk- / sk-proj-)' },
  { value: 'nvidia', label: 'NVIDIA NIM / NGC' },
  { value: 'github', label: 'GitHub (ghp_ / gho_ / ghu_)' },
  { value: 'google_cloud', label: 'Google Cloud (AIza...)' },
  { value: 'stripe', label: 'Stripe (sk_live_ / rk_live_)' },
  { value: 'azure', label: 'Microsoft Azure (AccountKey)' },
  { value: 'slack', label: 'Slack (xoxb- / xoxp-)' },
  { value: 'twilio', label: 'Twilio (SK...)' },
  { value: 'generic_api_key', label: 'Generic API Key Patterns' }
];

export default function ApiKeyIntelligence() {
  const [activeTab, setActiveTab] = useState('single_test'); // 'single_test', 'batch_test', 'test_history', 'benchmark', 'samples', 'stats'
  const [overview, setOverview] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [providers, setProviders] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkFeedback, setBenchmarkFeedback] = useState(null);

  // --- MODE A: SINGLE SAMPLE TESTING STATE ---
  const [singleProvider, setSingleProvider] = useState('');
  const [singleLabel, setSingleLabel] = useState('positive');
  const [singleSplit, setSingleSplit] = useState('test');
  const [singleOffset, setSingleOffset] = useState(0);
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleResult, setSingleResult] = useState(null);
  const [singleError, setSingleError] = useState(null);

  // --- MODE B: BATCH TESTING STATE ---
  const [batchProvider, setBatchProvider] = useState('');
  const [batchLabel, setBatchLabel] = useState('');
  const [batchCount, setBatchCount] = useState(50);
  const [batchSplit, setBatchSplit] = useState('test');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [batchResultsList, setBatchResultsList] = useState([]);
  const [batchResultsTotal, setBatchResultsTotal] = useState(0);
  const [batchResultsPage, setBatchResultsPage] = useState(0);
  const [batchError, setBatchError] = useState(null);

  // --- TEST HISTORY STATE ---
  const [historyList, setHistoryList] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedHistorySession, setSelectedHistorySession] = useState(null);
  const [historySessionResults, setHistorySessionResults] = useState([]);
  const [historySessionResultsTotal, setHistorySessionResultsTotal] = useState(0);
  const [historyResultsPage, setHistoryResultsPage] = useState(0);
  const [historyResultsLoading, setHistoryResultsLoading] = useState(false);

  // --- SAMPLE EXPLORER STATE ---
  const [samples, setSamples] = useState([]);
  const [samplesTotal, setSamplesTotal] = useState(0);
  const [samplesPage, setSamplesPage] = useState(0);
  const [samplesLimit] = useState(25);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedLabel, setSelectedLabel] = useState('');
  const [selectedSplit, setSelectedSplit] = useState('test');
  const [samplesLoading, setSamplesLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  // Fetch top-level data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [ovRes, bmRes, provRes, statRes] = await Promise.all([
        fetch(`${API_BASE}/overview`).then(r => r.json()),
        fetch(`${API_BASE}/benchmark`).then(r => r.json()),
        fetch(`${API_BASE}/providers`).then(r => r.json()),
        fetch(`${API_BASE}/statistics`).then(r => r.json()),
      ]);
      setOverview(ovRes);
      setBenchmark(bmRes);
      setProviders(provRes.providers || []);
      setStatistics(statRes);
    } catch (err) {
      console.error('Failed to load dataset intelligence:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch paginated samples
  const fetchSamples = async () => {
    setSamplesLoading(true);
    try {
      const params = new URLSearchParams({
        skip: (samplesPage * samplesLimit).toString(),
        limit: samplesLimit.toString(),
        split: selectedSplit,
      });
      if (selectedProvider) params.append('provider', selectedProvider);
      if (selectedLabel) params.append('label', selectedLabel);

      const res = await fetch(`${API_BASE}/samples?${params.toString()}`);
      const data = await res.json();
      setSamples(data.items || []);
      setSamplesTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to fetch samples:', err);
    } finally {
      setSamplesLoading(false);
    }
  };

  // Fetch test history
  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/test/history?limit=50`);
      const data = await res.json();
      setHistoryList(data.sessions || []);
      setHistoryTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to fetch test history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchHistory();
  }, []);

  useEffect(() => {
    if (activeTab === 'samples') {
      fetchSamples();
    } else if (activeTab === 'test_history') {
      fetchHistory();
    }
  }, [samplesPage, selectedProvider, selectedLabel, selectedSplit, activeTab]);

  // Execute single test
  const handleRunSingleTest = async (nextOffset = singleOffset) => {
    setSingleLoading(true);
    setSingleError(null);
    try {
      const payload = {
        split: singleSplit,
        offset: nextOffset
      };
      if (singleProvider) payload.provider = singleProvider;
      if (singleLabel) payload.label = singleLabel;

      const res = await fetch(`${API_BASE}/test/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with ${res.status}`);
      }
      const data = await res.json();
      setSingleResult(data);
      // Refresh history list in background
      fetchHistory();
    } catch (err) {
      setSingleError(err.message);
    } finally {
      setSingleLoading(false);
    }
  };

  const handleNextSample = () => {
    const next = singleOffset + 1;
    setSingleOffset(next);
    handleRunSingleTest(next);
  };

  // Execute batch test
  const handleRunBatchTest = async () => {
    setBatchLoading(true);
    setBatchError(null);
    setBatchResult(null);
    setBatchResultsList([]);
    try {
      const payload = {
        count: parseInt(batchCount, 10),
        split: batchSplit
      };
      if (batchProvider) payload.provider = batchProvider;
      if (batchLabel) payload.label = batchLabel;

      const res = await fetch(`${API_BASE}/test/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setBatchResult(data);

      // Fetch first page of results
      if (data.session_id) {
        fetchBatchResults(data.session_id, 0);
      }
      // Refresh history
      fetchHistory();
    } catch (err) {
      setBatchError(err.message);
    } finally {
      setBatchLoading(false);
    }
  };

  // Fetch individual results for a batch session
  const fetchBatchResults = async (sessionId, page = 0) => {
    try {
      const res = await fetch(`${API_BASE}/test/batch/${sessionId}/results?skip=${page * 20}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setBatchResultsList(data.items || []);
        setBatchResultsTotal(data.total || 0);
        setBatchResultsPage(page);
      }
    } catch (e) {
      console.error('Failed to load batch results:', e);
    }
  };

  // Inspect history session
  const handleInspectSession = async (session, page = 0) => {
    setSelectedHistorySession(session);
    setHistoryResultsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/test/batch/${session.session_id}/results?skip=${page * 20}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setHistorySessionResults(data.items || []);
        setHistorySessionResultsTotal(data.total || 0);
        setHistoryResultsPage(page);
      }
    } catch (err) {
      console.error('Failed to load session results:', err);
    } finally {
      setHistoryResultsLoading(false);
    }
  };

  // Run benchmark action
  const handleRunBenchmark = async () => {
    setBenchmarkLoading(true);
    setBenchmarkFeedback(null);
    try {
      const res = await fetch(`${API_BASE}/benchmark/run`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setBenchmark(data);
      const ovRes = await fetch(`${API_BASE}/overview`).then(r => r.json());
      setOverview(ovRes);

      setBenchmarkFeedback({
        type: 'success',
        message: `Benchmark evaluation completed in ${data.duration_ms} ms! F1: ${data.metrics.f1} | Precision: ${data.metrics.precision}% | Recall: ${data.metrics.recall}%`
      });
    } catch (err) {
      setBenchmarkFeedback({
        type: 'error',
        message: `Benchmark execution failed: ${err.message}`
      });
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getOutcomeBadge = (outcome) => {
    switch (outcome) {
      case 'correct_detection':
        return {
          bg: 'rgba(34, 197, 94, 0.16)',
          border: 'rgba(34, 197, 94, 0.4)',
          color: '#4ADE80',
          label: 'CORRECT DETECTION (TP)',
          icon: CheckCircle2
        };
      case 'correct_rejection':
        return {
          bg: 'rgba(56, 189, 248, 0.16)',
          border: 'rgba(56, 189, 248, 0.4)',
          color: '#38BDF8',
          label: 'CORRECT REJECTION (TN)',
          icon: CheckCircle2
        };
      case 'false_positive':
        return {
          bg: 'rgba(239, 68, 68, 0.16)',
          border: 'rgba(239, 68, 68, 0.4)',
          color: '#F87171',
          label: 'FALSE POSITIVE (FP)',
          icon: XCircle
        };
      case 'false_negative':
        return {
          bg: 'rgba(245, 158, 11, 0.16)',
          border: 'rgba(245, 158, 11, 0.4)',
          color: '#FBBF24',
          label: 'FALSE NEGATIVE (FN)',
          icon: AlertTriangle
        };
      default:
        return {
          bg: 'rgba(148, 163, 184, 0.16)',
          border: 'rgba(148, 163, 184, 0.4)',
          color: '#94A3B8',
          label: outcome?.toUpperCase() || 'UNKNOWN',
          icon: Info
        };
    }
  };

  if (loading && !overview) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#19D3FF' }}>
        <RefreshCw className="spin-icon" size={36} />
        <span style={{ marginLeft: '12px', fontSize: '1.1rem' }}>Loading API Key Intelligence...</span>
      </div>
    );
  }

  const metrics = benchmark?.metrics || { precision: 0, recall: 0, f1: 0, accuracy: 0, tp: 0, fp: 0, tn: 0, fn: 0 };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div 
        style={{
          background: 'linear-gradient(135deg, rgba(7, 24, 43, 0.95) 0%, rgba(13, 39, 68, 0.85) 100%)',
          border: '1px solid rgba(0, 200, 255, 0.25)',
          borderRadius: '14px',
          padding: '20px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          boxShadow: '0 8px 32px rgba(0, 10, 25, 0.4)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div 
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'rgba(25, 211, 255, 0.12)',
              border: '1.5px solid rgba(25, 211, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(25, 211, 255, 0.3)'
            }}
          >
            <Key size={26} color="#19D3FF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700, color: '#E8F1FF' }}>
                API Key Intelligence &amp; Testing Engine
              </h2>
              <span 
                style={{
                  background: 'rgba(25, 211, 255, 0.15)',
                  border: '1px solid rgba(25, 211, 255, 0.4)',
                  color: '#19D3FF',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '20px'
                }}
              >
                10,000 DATASET SAMPLES
              </span>
            </div>
            <p style={{ margin: '4px 0 0 0', color: '#8AA4C8', fontSize: '0.85rem' }}>
              Active detection engine testing against realistic API key patterns across 10 major cloud and SaaS providers.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleRunBenchmark}
            disabled={benchmarkLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: benchmarkLoading ? 'rgba(25, 211, 255, 0.3)' : 'linear-gradient(135deg, #00C8FF 0%, #0088FF 100%)',
              color: '#050D1F',
              border: 'none',
              padding: '10px 18px',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: benchmarkLoading ? 'not-allowed' : 'pointer',
              boxShadow: '0 0 20px rgba(0, 200, 255, 0.4)',
              transition: 'all 0.2s ease'
            }}
          >
            {benchmarkLoading ? (
              <>
                <RefreshCw size={18} className="spin-icon" />
                <span>EVALUATING 1,500 SAMPLES...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="#050D1F" />
                <span>RUN BENCHMARK (1,500)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Benchmark Feedback Banner */}
      {benchmarkFeedback && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            background: benchmarkFeedback.type === 'success' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${benchmarkFeedback.type === 'success' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            color: benchmarkFeedback.type === 'success' ? '#4ADE80' : '#F87171',
            fontSize: '0.86rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {benchmarkFeedback.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{benchmarkFeedback.message}</span>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid rgba(25, 211, 255, 0.15)', paddingBottom: '12px', flexWrap: 'wrap' }}>
        {[
          { id: 'single_test', label: 'Single Key Detection', icon: ShieldCheck, badge: 'Mode A' },
          { id: 'batch_test', label: 'Batch Security Testing', icon: Cpu, badge: 'Mode B' },
          { id: 'test_history', label: 'Test Run History', icon: Layers, badge: `${historyTotal}` },
          { id: 'benchmark', label: 'Full Benchmark Suite', icon: BarChart2 },
          { id: 'samples', label: 'Dataset Explorer', icon: Search },
          { id: 'stats', label: 'Dataset Statistics & Governance', icon: Database },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: isActive ? 'rgba(25, 211, 255, 0.18)' : 'transparent',
                color: isActive ? '#19D3FF' : '#8AA4C8',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.88rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span style={{
                  fontSize: '0.7rem',
                  padding: '1px 6px',
                  borderRadius: '10px',
                  background: isActive ? 'rgba(25, 211, 255, 0.25)' : 'rgba(255, 255, 255, 0.08)',
                  color: isActive ? '#19D3FF' : '#94A3B8'
                }}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB: MODE A - SINGLE SAMPLE TESTING */}
      {/* ========================================================================= */}
      {activeTab === 'single_test' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Controls Bar */}
          <div style={boxCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={20} color="#19D3FF" />
                  <span>Mode A: Single Key Detection &amp; Explainability</span>
                </h3>
                <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem' }}>
                  Select provider &amp; label criteria, execute the detection engine against exactly one sample, and inspect regex &amp; entropy explanations.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleRunSingleTest()}
                  disabled={singleLoading}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: singleLoading ? 'rgba(25, 211, 255, 0.2)' : 'linear-gradient(135deg, #00C8FF 0%, #0088FF 100%)',
                    color: '#050D1F',
                    border: 'none',
                    padding: '9px 18px',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.86rem',
                    cursor: singleLoading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 0 16px rgba(0, 200, 255, 0.35)'
                  }}
                >
                  {singleLoading ? <RefreshCw size={16} className="spin-icon" /> : <Play size={16} fill="#050D1F" />}
                  <span>RUN DETECTION TEST</span>
                </button>

                <button
                  onClick={handleNextSample}
                  disabled={singleLoading}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: 'rgba(25, 211, 255, 0.1)',
                    border: '1px solid rgba(25, 211, 255, 0.35)',
                    color: '#19D3FF',
                    padding: '9px 16px',
                    borderRadius: '8px',
                    fontWeight: 600,
                    fontSize: '0.86rem',
                    cursor: singleLoading ? 'not-allowed' : 'pointer'
                  }}
                >
                  <span>NEXT SAMPLE</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>

            {/* Filters Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  PROVIDER TARGET
                </label>
                <select
                  value={singleProvider}
                  onChange={(e) => { setSingleProvider(e.target.value); setSingleOffset(0); }}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  {PROVIDER_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  SAMPLE LABEL TYPE
                </label>
                <select
                  value={singleLabel}
                  onChange={(e) => { setSingleLabel(e.target.value); setSingleOffset(0); }}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  <option value="">Any Label (Positive or Negative)</option>
                  <option value="positive">Positive (Valid Signature Format)</option>
                  <option value="negative">Negative (Dummy / Lookalike / Non-key)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  DATASET SPLIT
                </label>
                <select
                  value={singleSplit}
                  onChange={(e) => { setSingleSplit(e.target.value); setSingleOffset(0); }}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  <option value="test">Held-Out Test Split (1,500 samples)</option>
                  <option value="validation">Validation Split (1,500 samples)</option>
                  <option value="train">Training Split (7,000 samples)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  CURRENT SAMPLE OFFSET
                </label>
                <div style={{
                  background: '#050D1F',
                  border: '1px solid rgba(25, 211, 255, 0.2)',
                  borderRadius: '6px',
                  padding: '7px 12px',
                  color: '#38BDF8',
                  fontSize: '0.84rem',
                  fontWeight: 600
                }}>
                  Index: #{singleOffset}
                </div>
              </div>
            </div>
          </div>

          {singleError && (
            <div style={{
              padding: '12px 18px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#F87171',
              fontSize: '0.86rem'
            }}>
              {singleError}
            </div>
          )}

          {/* Test Outcome Display */}
          {singleResult && (() => {
            const outcomeBadge = getOutcomeBadge(singleResult.test_outcome);
            const OutcomeIcon = outcomeBadge.icon;

            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Result Header Badge Card */}
                <div style={{
                  ...boxCardStyle,
                  background: 'linear-gradient(135deg, #091C33 0%, #0E294B 100%)',
                  border: `1.5px solid ${outcomeBadge.border}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        padding: '10px',
                        borderRadius: '10px',
                        background: outcomeBadge.bg,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <OutcomeIcon size={24} color={outcomeBadge.color} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            background: outcomeBadge.bg,
                            border: `1px solid ${outcomeBadge.border}`,
                            color: outcomeBadge.color,
                            fontSize: '0.8rem',
                            fontWeight: 700,
                            padding: '3px 10px',
                            borderRadius: '20px'
                          }}>
                            {outcomeBadge.label}
                          </span>
                          <span style={{ color: '#8AA4C8', fontSize: '0.8rem' }}>
                            Sample ID: <code style={{ color: '#E8F1FF' }}>{singleResult.sample_id}</code>
                          </span>
                        </div>
                        <p style={{ margin: '4px 0 0 0', color: '#E8F1FF', fontSize: '0.92rem', fontWeight: 600 }}>
                          {singleResult.notes}
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.72rem', color: '#8AA4C8', textTransform: 'uppercase' }}>EXECUTION TIME</div>
                        <div style={{ fontSize: '1.15rem', color: '#00E5FF', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                          <Clock size={14} />
                          <span>{singleResult.execution_time_ms} ms</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Masked Sample Representation */}
                <div style={boxCardStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.78rem', color: '#8AA4C8', fontWeight: 600 }}>
                      PROTECTED MASKED SAMPLE (RAW TOKEN NEVER EXPOSED)
                    </span>
                    <button
                      onClick={() => copyToClipboard(singleResult.masked_sample, 'single-sample')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: copiedId === 'single-sample' ? '#4ADE80' : '#8AA4C8',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.76rem'
                      }}
                    >
                      {copiedId === 'single-sample' ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copiedId === 'single-sample' ? 'Copied' : 'Copy Masked'}</span>
                    </button>
                  </div>
                  <pre style={{
                    margin: 0,
                    padding: '12px 16px',
                    background: '#040B17',
                    borderRadius: '8px',
                    border: '1px solid rgba(25, 211, 255, 0.25)',
                    color: '#38BDF8',
                    fontFamily: 'monospace',
                    fontSize: '0.88rem',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all'
                  }}>
                    {singleResult.masked_sample}
                  </pre>
                </div>

                {/* Prediction vs Ground Truth Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                  {/* Ground Truth */}
                  <div style={{ ...boxCardStyle, borderLeft: '3px solid #38BDF8' }}>
                    <div style={{ fontSize: '0.75rem', color: '#8AA4C8', fontWeight: 700, marginBottom: '10px' }}>
                      GROUND TRUTH (DATASET SPECIFICATION)
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Expected Provider:</span>
                        <strong style={{ color: '#E8F1FF', textTransform: 'uppercase' }}>{singleResult.expected_provider}</strong>
                      </div>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Expected Label:</span>
                        <strong style={{ color: singleResult.expected_label === 'positive' ? '#4ADE80' : '#94A3B8' }}>
                          {singleResult.expected_label.toUpperCase()}
                        </strong>
                      </div>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Classification:</span>
                        <span style={{ color: '#8AA4C8' }}>{singleResult.expected_label === 'positive' ? 'Secret Credential' : 'Negative Non-Secret'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Detection Engine Result */}
                  <div style={{
                    ...boxCardStyle,
                    borderLeft: `3px solid ${singleResult.is_correct ? '#22C55E' : '#EF4444'}`
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#8AA4C8', fontWeight: 700, marginBottom: '10px' }}>
                      DETECTION ENGINE PREDICTION
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Detected Provider:</span>
                        <strong style={{ color: singleResult.detected_provider ? '#00E5FF' : '#94A3B8', textTransform: 'uppercase' }}>
                          {singleResult.detected_provider || 'NONE (NO MATCH)'}
                        </strong>
                      </div>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Predicted Label:</span>
                        <strong style={{ color: singleResult.predicted_label === 'positive' ? '#4ADE80' : '#94A3B8' }}>
                          {singleResult.predicted_label.toUpperCase()}
                        </strong>
                      </div>
                      <div style={rowStyle}>
                        <span style={{ color: '#8AA4C8' }}>Prediction Status:</span>
                        <strong style={{ color: singleResult.is_correct ? '#4ADE80' : '#F87171' }}>
                          {singleResult.is_correct ? 'ACCURATE (PASS)' : 'INCORRECT (FAIL)'}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detection Explanation Box */}
                <div style={{ ...boxCardStyle, background: 'linear-gradient(135deg, #061528 0%, #0A203B 100%)' }}>
                  <h4 style={{ margin: '0 0 10px 0', fontSize: '0.92rem', color: '#00E5FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={16} />
                    <span>Detection Engine Reason &amp; Entropy Analysis</span>
                  </h4>
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    background: '#030812',
                    border: '1px solid rgba(25, 211, 255, 0.2)',
                    color: '#E8F1FF',
                    fontSize: '0.86rem',
                    lineHeight: 1.6
                  }}>
                    {singleResult.detection_reason}
                  </div>
                  {singleResult.confidence_score && (
                    <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#8AA4C8' }}>
                      Calculated Shannon Information Entropy: <strong style={{ color: '#38BDF8' }}>{singleResult.confidence_score} bits</strong> (Threshold: &gt;3.0 bits for random secrets).
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          {!singleResult && !singleLoading && (
            <div style={{
              ...boxCardStyle,
              textAlign: 'center',
              padding: '48px 24px',
              color: '#8AA4C8'
            }}>
              <ShieldCheck size={48} color="rgba(25, 211, 255, 0.3)" style={{ margin: '0 auto 16px auto' }} />
              <h4 style={{ margin: '0 0 8px 0', color: '#E8F1FF', fontSize: '1.1rem' }}>No Sample Tested Yet</h4>
              <p style={{ maxWidth: '500px', margin: '0 auto 16px auto', fontSize: '0.85rem' }}>
                Select your desired provider and label filter above, then click <strong>Run Detection Test</strong> to evaluate a sample through the active detection engine.
              </p>
              <button
                onClick={() => handleRunSingleTest()}
                style={{
                  background: 'linear-gradient(135deg, #00C8FF 0%, #0088FF 100%)',
                  color: '#050D1F',
                  border: 'none',
                  padding: '9px 20px',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.86rem',
                  cursor: 'pointer'
                }}
              >
                TEST FIRST SAMPLE
              </button>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: MODE B - BATCH TESTING */}
      {/* ========================================================================= */}
      {activeTab === 'batch_test' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Batch Configuration Card */}
          <div style={boxCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={20} color="#19D3FF" />
                  <span>Mode B: Batch Security Testing &amp; Concurrency Guard</span>
                </h3>
                <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem' }}>
                  Execute detection against custom batch slices (10 to 500 samples) with atomic concurrency locking and per-provider metric computation.
                </p>
              </div>

              <button
                onClick={handleRunBatchTest}
                disabled={batchLoading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: batchLoading ? 'rgba(25, 211, 255, 0.2)' : 'linear-gradient(135deg, #00C8FF 0%, #0088FF 100%)',
                  color: '#050D1F',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.88rem',
                  cursor: batchLoading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 0 16px rgba(0, 200, 255, 0.35)'
                }}
              >
                {batchLoading ? <RefreshCw size={16} className="spin-icon" /> : <Play size={16} fill="#050D1F" />}
                <span>{batchLoading ? `EVALUATING ${batchCount} SAMPLES...` : 'START BATCH TEST'}</span>
              </button>
            </div>

            {/* Batch Filter Settings */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  PROVIDER FILTER
                </label>
                <select
                  value={batchProvider}
                  onChange={(e) => setBatchProvider(e.target.value)}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  {PROVIDER_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  CATEGORY / LABEL
                </label>
                <select
                  value={batchLabel}
                  onChange={(e) => setBatchLabel(e.target.value)}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  <option value="">All Categories (Mixed)</option>
                  <option value="positive">Positive Only (Real format)</option>
                  <option value="negative">Negative Only (Lookalike/Dummy)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  SAMPLE COUNT
                </label>
                <select
                  value={batchCount}
                  onChange={(e) => setBatchCount(e.target.value)}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  <option value="10">10 Samples (Fast Probe)</option>
                  <option value="50">50 Samples (Standard)</option>
                  <option value="100">100 Samples (Comprehensive)</option>
                  <option value="250">250 Samples (Deep Audit)</option>
                  <option value="500">500 Samples (Stress Test)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#8AA4C8', marginBottom: '6px', fontWeight: 600 }}>
                  DATASET SPLIT
                </label>
                <select
                  value={batchSplit}
                  onChange={(e) => setBatchSplit(e.target.value)}
                  style={{ ...selectStyle, width: '100%' }}
                >
                  <option value="test">Held-Out Test Split (1,500 samples)</option>
                  <option value="validation">Validation Split (1,500 samples)</option>
                  <option value="train">Training Split (7,000 samples)</option>
                </select>
              </div>
            </div>
          </div>

          {batchError && (
            <div style={{
              padding: '12px 18px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#F87171',
              fontSize: '0.86rem'
            }}>
              {batchError}
            </div>
          )}

          {/* Batch Metrics Results */}
          {batchResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Top KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                <div style={kpiCardStyle}>
                  <div style={{ color: '#8AA4C8', fontSize: '0.75rem', fontWeight: 600 }}>ACCURACY</div>
                  <div style={{ color: '#00E5FF', fontSize: '1.8rem', fontWeight: 800, margin: '4px 0' }}>
                    {batchResult.metrics.accuracy}%
                  </div>
                  <div style={{ color: '#8AA4C8', fontSize: '0.72rem' }}>
                    {(batchResult.metrics.tp + batchResult.metrics.tn)} / {batchResult.completed_sample_count} Correct
                  </div>
                </div>

                <div style={kpiCardStyle}>
                  <div style={{ color: '#8AA4C8', fontSize: '0.75rem', fontWeight: 600 }}>F1 SCORE</div>
                  <div style={{ color: '#38BDF8', fontSize: '1.8rem', fontWeight: 800, margin: '4px 0' }}>
                    {batchResult.metrics.f1}
                  </div>
                  <div style={{ color: '#8AA4C8', fontSize: '0.72rem' }}>Harmonic Mean of Precision &amp; Recall</div>
                </div>

                <div style={kpiCardStyle}>
                  <div style={{ color: '#8AA4C8', fontSize: '0.75rem', fontWeight: 600 }}>PRECISION</div>
                  <div style={{ color: '#4ADE80', fontSize: '1.8rem', fontWeight: 800, margin: '4px 0' }}>
                    {batchResult.metrics.precision}%
                  </div>
                  <div style={{ color: '#8AA4C8', fontSize: '0.72rem' }}>TP: {batchResult.metrics.tp} | FP: {batchResult.metrics.fp}</div>
                </div>

                <div style={kpiCardStyle}>
                  <div style={{ color: '#8AA4C8', fontSize: '0.75rem', fontWeight: 600 }}>RECALL</div>
                  <div style={{ color: '#A78BFA', fontSize: '1.8rem', fontWeight: 800, margin: '4px 0' }}>
                    {batchResult.metrics.recall}%
                  </div>
                  <div style={{ color: '#8AA4C8', fontSize: '0.72rem' }}>TP: {batchResult.metrics.tp} | FN: {batchResult.metrics.fn}</div>
                </div>

                <div style={kpiCardStyle}>
                  <div style={{ color: '#8AA4C8', fontSize: '0.75rem', fontWeight: 600 }}>DURATION</div>
                  <div style={{ color: '#E8F1FF', fontSize: '1.8rem', fontWeight: 800, margin: '4px 0' }}>
                    {batchResult.duration_ms} ms
                  </div>
                  <div style={{ color: '#8AA4C8', fontSize: '0.72rem' }}>
                    ~{(batchResult.duration_ms / Math.max(batchResult.completed_sample_count, 1)).toFixed(2)} ms / sample
                  </div>
                </div>
              </div>

              {/* Confusion Matrix & Provider Breakdown */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {/* 2x2 Confusion Matrix */}
                <div style={boxCardStyle}>
                  <h4 style={{ margin: '0 0 14px 0', fontSize: '0.95rem', color: '#E8F1FF' }}>
                    Confusion Matrix ({batchResult.completed_sample_count} Samples)
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div style={{ background: 'rgba(34, 197, 94, 0.12)', border: '1px solid rgba(34, 197, 94, 0.3)', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ color: '#4ADE80', fontSize: '1.6rem', fontWeight: 800 }}>{batchResult.metrics.tp}</div>
                      <div style={{ color: '#E8F1FF', fontSize: '0.78rem', fontWeight: 600, marginTop: '2px' }}>TRUE POSITIVE (TP)</div>
                      <div style={{ color: '#8AA4C8', fontSize: '0.7rem' }}>Detected real secret correctly</div>
                    </div>
                    <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ color: '#F87171', fontSize: '1.6rem', fontWeight: 800 }}>{batchResult.metrics.fp}</div>
                      <div style={{ color: '#E8F1FF', fontSize: '0.78rem', fontWeight: 600, marginTop: '2px' }}>FALSE POSITIVE (FP)</div>
                      <div style={{ color: '#8AA4C8', fontSize: '0.7rem' }}>Flagged dummy/lookalike as secret</div>
                    </div>
                    <div style={{ background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ color: '#FBBF24', fontSize: '1.6rem', fontWeight: 800 }}>{batchResult.metrics.fn}</div>
                      <div style={{ color: '#E8F1FF', fontSize: '0.78rem', fontWeight: 600, marginTop: '2px' }}>FALSE NEGATIVE (FN)</div>
                      <div style={{ color: '#8AA4C8', fontSize: '0.7rem' }}>Missed a secret format</div>
                    </div>
                    <div style={{ background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ color: '#38BDF8', fontSize: '1.6rem', fontWeight: 800 }}>{batchResult.metrics.tn}</div>
                      <div style={{ color: '#E8F1FF', fontSize: '0.78rem', fontWeight: 600, marginTop: '2px' }}>TRUE NEGATIVE (TN)</div>
                      <div style={{ color: '#8AA4C8', fontSize: '0.7rem' }}>Rejected dummy safely</div>
                    </div>
                  </div>
                </div>

                {/* Per-Provider Table */}
                <div style={boxCardStyle}>
                  <h4 style={{ margin: '0 0 14px 0', fontSize: '0.95rem', color: '#E8F1FF' }}>
                    Per-Provider Breakdown
                  </h4>
                  <div style={{ maxHeight: '210px', overflowY: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ color: '#8AA4C8', borderBottom: '1px solid rgba(25, 211, 255, 0.15)' }}>
                          <th style={{ padding: '6px 8px' }}>PROVIDER</th>
                          <th style={{ padding: '6px 8px' }}>SAMPLES</th>
                          <th style={{ padding: '6px 8px' }}>PREC</th>
                          <th style={{ padding: '6px 8px' }}>REC</th>
                          <th style={{ padding: '6px 8px' }}>F1</th>
                          <th style={{ padding: '6px 8px' }}>ACC</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchResult.per_provider?.map(p => (
                          <tr key={p.provider} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                            <td style={{ padding: '6px 8px', color: '#38BDF8', fontWeight: 600, textTransform: 'uppercase' }}>{p.provider}</td>
                            <td style={{ padding: '6px 8px', color: '#E8F1FF' }}>{p.samples}</td>
                            <td style={{ padding: '6px 8px', color: '#4ADE80' }}>{p.precision}%</td>
                            <td style={{ padding: '6px 8px', color: '#A78BFA' }}>{p.recall}%</td>
                            <td style={{ padding: '6px 8px', color: '#00E5FF', fontWeight: 600 }}>{p.f1}</td>
                            <td style={{ padding: '6px 8px', color: '#E8F1FF' }}>{p.accuracy}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Individual Samples Explorer for this Batch */}
              {batchResultsList.length > 0 && (
                <div style={boxCardStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#E8F1FF' }}>
                      Individual Sample Results ({batchResultsTotal} Total)
                    </h4>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => fetchBatchResults(batchResult.session_id, batchResultsPage - 1)}
                        disabled={batchResultsPage === 0}
                        style={pageBtnStyle(batchResultsPage === 0)}
                      >
                        Previous
                      </button>
                      <span style={{ color: '#8AA4C8', fontSize: '0.78rem', alignSelf: 'center' }}>
                        Page {batchResultsPage + 1} of {Math.ceil(batchResultsTotal / 20) || 1}
                      </span>
                      <button
                        onClick={() => fetchBatchResults(batchResult.session_id, batchResultsPage + 1)}
                        disabled={(batchResultsPage + 1) * 20 >= batchResultsTotal}
                        style={pageBtnStyle((batchResultsPage + 1) * 20 >= batchResultsTotal)}
                      >
                        Next
                      </button>
                    </div>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(25, 211, 255, 0.2)', color: '#8AA4C8' }}>
                          <th style={{ padding: '8px 10px' }}>SAMPLE ID</th>
                          <th style={{ padding: '8px 10px' }}>MASKED CONTENT</th>
                          <th style={{ padding: '8px 10px' }}>EXPECTED</th>
                          <th style={{ padding: '8px 10px' }}>DETECTED</th>
                          <th style={{ padding: '8px 10px' }}>OUTCOME</th>
                          <th style={{ padding: '8px 10px' }}>TIME</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchResultsList.map(item => {
                          const badge = getOutcomeBadge(item.test_outcome);
                          return (
                            <tr key={item.result_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                              <td style={{ padding: '8px 10px', color: '#38BDF8', fontFamily: 'monospace' }}>{item.sample_id}</td>
                              <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#CBD5E1', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {item.masked_sample}
                              </td>
                              <td style={{ padding: '8px 10px', textTransform: 'uppercase' }}>
                                <span style={{ color: '#E8F1FF' }}>{item.expected_provider}</span> ({item.expected_label})
                              </td>
                              <td style={{ padding: '8px 10px', textTransform: 'uppercase', color: item.detected_provider ? '#00E5FF' : '#94A3B8' }}>
                                {item.detected_provider || 'None'}
                              </td>
                              <td style={{ padding: '8px 10px' }}>
                                <span style={{
                                  background: badge.bg,
                                  border: `1px solid ${badge.border}`,
                                  color: badge.color,
                                  fontSize: '0.72rem',
                                  padding: '2px 8px',
                                  borderRadius: '12px',
                                  fontWeight: 600
                                }}>
                                  {badge.label}
                                </span>
                              </td>
                              <td style={{ padding: '8px 10px', color: '#8AA4C8' }}>{item.execution_time_ms} ms</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: TEST RUN HISTORY & INSPECTION */}
      {/* ========================================================================= */}
      {activeTab === 'test_history' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={boxCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={20} color="#19D3FF" />
                  <span>Test Run History ({historyTotal} Saved Sessions)</span>
                </h3>
                <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem' }}>
                  Persistent audit log of all single-sample and batch tests executed in SQLite.
                </p>
              </div>

              <button
                onClick={fetchHistory}
                disabled={historyLoading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(25, 211, 255, 0.1)',
                  border: '1px solid rgba(25, 211, 255, 0.3)',
                  color: '#19D3FF',
                  padding: '7px 14px',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  cursor: 'pointer'
                }}
              >
                <RefreshCw size={14} className={historyLoading ? 'spin-icon' : ''} />
                <span>Refresh History</span>
              </button>
            </div>

            {/* Sessions Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(25, 211, 255, 0.2)', color: '#8AA4C8' }}>
                    <th style={{ padding: '8px 10px' }}>SESSION ID</th>
                    <th style={{ padding: '8px 10px' }}>MODE</th>
                    <th style={{ padding: '8px 10px' }}>PROVIDER</th>
                    <th style={{ padding: '8px 10px' }}>LABEL</th>
                    <th style={{ padding: '8px 10px' }}>SAMPLES</th>
                    <th style={{ padding: '8px 10px' }}>ACCURACY</th>
                    <th style={{ padding: '8px 10px' }}>F1</th>
                    <th style={{ padding: '8px 10px' }}>STARTED</th>
                    <th style={{ padding: '8px 10px' }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {historyList.map(s => {
                    const isSelected = selectedHistorySession?.session_id === s.session_id;
                    return (
                      <tr
                        key={s.session_id}
                        style={{
                          borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                          background: isSelected ? 'rgba(25, 211, 255, 0.08)' : 'transparent'
                        }}
                      >
                        <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#38BDF8' }}>
                          {s.session_id.slice(0, 8)}...
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '10px',
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            background: s.test_mode === 'single' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(192, 132, 252, 0.15)',
                            color: s.test_mode === 'single' ? '#38BDF8' : '#C084FC',
                            border: `1px solid ${s.test_mode === 'single' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(192, 132, 252, 0.3)'}`
                          }}>
                            {s.test_mode.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '8px 10px', textTransform: 'uppercase', color: '#E8F1FF' }}>
                          {s.provider_filter || 'ALL'}
                        </td>
                        <td style={{ padding: '8px 10px', color: '#8AA4C8' }}>
                          {s.label_filter || 'ALL'}
                        </td>
                        <td style={{ padding: '8px 10px', color: '#E8F1FF', fontWeight: 600 }}>
                          {s.completed_sample_count}
                        </td>
                        <td style={{ padding: '8px 10px', color: '#00E5FF', fontWeight: 700 }}>
                          {s.accuracy}%
                        </td>
                        <td style={{ padding: '8px 10px', color: '#4ADE80' }}>
                          {s.f1}
                        </td>
                        <td style={{ padding: '8px 10px', color: '#8AA4C8', fontSize: '0.75rem' }}>
                          {new Date(s.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <button
                            onClick={() => handleInspectSession(s, 0)}
                            style={{
                              background: isSelected ? 'rgba(25, 211, 255, 0.25)' : 'rgba(255, 255, 255, 0.06)',
                              border: '1px solid rgba(25, 211, 255, 0.3)',
                              color: '#19D3FF',
                              padding: '4px 10px',
                              borderRadius: '4px',
                              fontSize: '0.74rem',
                              cursor: 'pointer'
                            }}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {historyList.length === 0 && !historyLoading && (
                    <tr>
                      <td colSpan="9" style={{ padding: '24px', textAlign: 'center', color: '#8AA4C8' }}>
                        No test sessions recorded yet. Run a single test or batch test to begin tracking history.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Inspected Session Details */}
          {selectedHistorySession && (
            <div style={boxCardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#E8F1FF' }}>
                    Session Inspection: <code style={{ color: '#00E5FF' }}>{selectedHistorySession.session_id}</code>
                  </h4>
                  <div style={{ fontSize: '0.8rem', color: '#8AA4C8' }}>
                    Mode: <strong style={{ color: '#E8F1FF' }}>{selectedHistorySession.test_mode}</strong> | Provider: <strong style={{ color: '#E8F1FF' }}>{selectedHistorySession.provider_filter || 'All'}</strong> | Accuracy: <strong style={{ color: '#4ADE80' }}>{selectedHistorySession.accuracy}%</strong> | F1: <strong style={{ color: '#38BDF8' }}>{selectedHistorySession.f1}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleInspectSession(selectedHistorySession, historyResultsPage - 1)}
                    disabled={historyResultsPage === 0 || historyResultsLoading}
                    style={pageBtnStyle(historyResultsPage === 0 || historyResultsLoading)}
                  >
                    Previous
                  </button>
                  <span style={{ color: '#8AA4C8', fontSize: '0.78rem', alignSelf: 'center' }}>
                    Page {historyResultsPage + 1} of {Math.ceil(historySessionResultsTotal / 20) || 1}
                  </span>
                  <button
                    onClick={() => handleInspectSession(selectedHistorySession, historyResultsPage + 1)}
                    disabled={(historyResultsPage + 1) * 20 >= historySessionResultsTotal || historyResultsLoading}
                    style={pageBtnStyle((historyResultsPage + 1) * 20 >= historySessionResultsTotal || historyResultsLoading)}
                  >
                    Next
                  </button>
                </div>
              </div>

              {/* Sample Results in Session */}
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(25, 211, 255, 0.2)', color: '#8AA4C8' }}>
                      <th style={{ padding: '8px 10px' }}>SAMPLE ID</th>
                      <th style={{ padding: '8px 10px' }}>MASKED CONTENT</th>
                      <th style={{ padding: '8px 10px' }}>EXPECTED</th>
                      <th style={{ padding: '8px 10px' }}>DETECTED</th>
                      <th style={{ padding: '8px 10px' }}>OUTCOME</th>
                      <th style={{ padding: '8px 10px' }}>EXPLANATION</th>
                      <th style={{ padding: '8px 10px' }}>TIME</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historySessionResults.map(item => {
                      const badge = getOutcomeBadge(item.test_outcome);
                      return (
                        <tr key={item.result_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                          <td style={{ padding: '8px 10px', color: '#38BDF8', fontFamily: 'monospace' }}>{item.sample_id}</td>
                          <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#CBD5E1', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {item.masked_sample}
                          </td>
                          <td style={{ padding: '8px 10px', textTransform: 'uppercase' }}>
                            <span style={{ color: '#E8F1FF' }}>{item.expected_provider}</span> ({item.expected_label})
                          </td>
                          <td style={{ padding: '8px 10px', textTransform: 'uppercase', color: item.detected_provider ? '#00E5FF' : '#94A3B8' }}>
                            {item.detected_provider || 'None'}
                          </td>
                          <td style={{ padding: '8px 10px' }}>
                            <span style={{
                              background: badge.bg,
                              border: `1px solid ${badge.border}`,
                              color: badge.color,
                              fontSize: '0.72rem',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontWeight: 600
                            }}>
                              {badge.label}
                            </span>
                          </td>
                          <td style={{ padding: '8px 10px', color: '#94A3B8', fontSize: '0.76rem', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {item.detection_reason}
                          </td>
                          <td style={{ padding: '8px 10px', color: '#8AA4C8' }}>{item.execution_time_ms} ms</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: BENCHMARK & METRICS */}
      {/* ========================================================================= */}
      {activeTab === 'benchmark' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Top KPI Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px' }}>
            <div style={kpiCardStyle}>
              <div style={{ color: '#8AA4C8', fontSize: '0.8rem', fontWeight: 600 }}>PRECISION (TP / TP+FP)</div>
              <div style={{ color: '#00E5FF', fontSize: '1.9rem', fontWeight: 800, margin: '6px 0 2px 0' }}>
                {metrics.precision}%
              </div>
              <div style={{ color: '#8AA4C8', fontSize: '0.74rem' }}>
                True Positives: {metrics.tp} | False Positives: {metrics.fp}
              </div>
            </div>

            <div style={kpiCardStyle}>
              <div style={{ color: '#8AA4C8', fontSize: '0.8rem', fontWeight: 600 }}>RECALL (TP / TP+FN)</div>
              <div style={{ color: '#38BDF8', fontSize: '1.9rem', fontWeight: 800, margin: '6px 0 2px 0' }}>
                {metrics.recall}%
              </div>
              <div style={{ color: '#8AA4C8', fontSize: '0.74rem' }}>
                Identified: {metrics.tp} | Missed: {metrics.fn}
              </div>
            </div>

            <div style={kpiCardStyle}>
              <div style={{ color: '#8AA4C8', fontSize: '0.8rem', fontWeight: 600 }}>F1 SCORE</div>
              <div style={{ color: '#A78BFA', fontSize: '1.9rem', fontWeight: 800, margin: '6px 0 2px 0' }}>
                {metrics.f1}
              </div>
              <div style={{ color: '#8AA4C8', fontSize: '0.74rem' }}>
                Harmonic mean across balanced classes
              </div>
            </div>

            <div style={kpiCardStyle}>
              <div style={{ color: '#8AA4C8', fontSize: '0.8rem', fontWeight: 600 }}>OVERALL ACCURACY</div>
              <div style={{ color: '#34D399', fontSize: '1.9rem', fontWeight: 800, margin: '6px 0 2px 0' }}>
                {metrics.accuracy}%
              </div>
              <div style={{ color: '#8AA4C8', fontSize: '0.74rem' }}>
                Held-out Test Split ({benchmark?.total_samples || 1500} samples)
              </div>
            </div>
          </div>

          {/* Provider Performance Breakdown Table */}
          <div style={boxCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={20} color="#19D3FF" />
                  <span>Provider-Specific Detection Performance</span>
                </h3>
                <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.82rem' }}>
                  Benchmark evaluation results broken down by each secret scanning pattern category.
                </p>
              </div>
              <span style={{ color: '#8AA4C8', fontSize: '0.8rem' }}>
                Duration: <strong style={{ color: '#E8F1FF' }}>{benchmark?.duration_ms || 0} ms</strong>
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(25, 211, 255, 0.2)', color: '#8AA4C8' }}>
                    <th style={{ padding: '10px 12px' }}>PROVIDER</th>
                    <th style={{ padding: '10px 12px' }}>SAMPLES</th>
                    <th style={{ padding: '10px 12px' }}>TP</th>
                    <th style={{ padding: '10px 12px' }}>FP</th>
                    <th style={{ padding: '10px 12px' }}>TN</th>
                    <th style={{ padding: '10px 12px' }}>FN</th>
                    <th style={{ padding: '10px 12px' }}>PRECISION</th>
                    <th style={{ padding: '10px 12px' }}>RECALL</th>
                    <th style={{ padding: '10px 12px' }}>F1 SCORE</th>
                    <th style={{ padding: '10px 12px' }}>ACCURACY</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmark?.per_provider?.map((row) => (
                    <tr 
                      key={row.provider}
                      style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(25, 211, 255, 0.04)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '10px 12px', fontWeight: 600, color: '#38BDF8', textTransform: 'uppercase' }}>
                        {row.provider}
                      </td>
                      <td style={{ padding: '10px 12px', color: '#E8F1FF' }}>{row.samples}</td>
                      <td style={{ padding: '10px 12px', color: '#4ADE80' }}>{row.tp}</td>
                      <td style={{ padding: '10px 12px', color: '#F87171' }}>{row.fp}</td>
                      <td style={{ padding: '10px 12px', color: '#38BDF8' }}>{row.tn}</td>
                      <td style={{ padding: '10px 12px', color: '#FBBF24' }}>{row.fn}</td>
                      <td style={{ padding: '10px 12px', color: '#00E5FF' }}>{row.precision}%</td>
                      <td style={{ padding: '10px 12px', color: '#38BDF8' }}>{row.recall}%</td>
                      <td style={{ padding: '10px 12px', fontWeight: 700, color: '#A78BFA' }}>{row.f1}</td>
                      <td style={{ padding: '10px 12px', color: '#34D399' }}>{row.accuracy}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: SAMPLES EXPLORER */}
      {/* ========================================================================= */}
      {activeTab === 'samples' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Filter Bar */}
          <div style={boxCardStyle}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: '#8AA4C8', marginBottom: '4px' }}>
                    SPLIT
                  </label>
                  <select
                    value={selectedSplit}
                    onChange={(e) => { setSelectedSplit(e.target.value); setSamplesPage(0); }}
                    style={selectStyle}
                  >
                    <option value="test">Held-out Test (1,500)</option>
                    <option value="validation">Validation (1,500)</option>
                    <option value="train">Train (7,000)</option>
                    <option value="master">Master (10,000)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: '#8AA4C8', marginBottom: '4px' }}>
                    PROVIDER
                  </label>
                  <select
                    value={selectedProvider}
                    onChange={(e) => { setSelectedProvider(e.target.value); setSamplesPage(0); }}
                    style={selectStyle}
                  >
                    <option value="">All Providers ({providers.length})</option>
                    {providers.map(p => (
                      <option key={p.provider} value={p.provider}>{p.provider.toUpperCase()} ({p.sample_count})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', color: '#8AA4C8', marginBottom: '4px' }}>
                    LABEL
                  </label>
                  <select
                    value={selectedLabel}
                    onChange={(e) => { setSelectedLabel(e.target.value); setSamplesPage(0); }}
                    style={selectStyle}
                  >
                    <option value="">All Labels</option>
                    <option value="positive">Positive (True Secret)</option>
                    <option value="negative">Negative (Lookalike / Dummy)</option>
                  </select>
                </div>
              </div>

              <div style={{ color: '#8AA4C8', fontSize: '0.84rem' }}>
                Showing <strong>{samples.length}</strong> of <strong>{samplesTotal}</strong> matched samples
              </div>
            </div>
          </div>

          {/* Masked Samples Table */}
          <div style={boxCardStyle}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.84rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(25, 211, 255, 0.2)', color: '#8AA4C8' }}>
                    <th style={{ padding: '8px 10px' }}>SAMPLE ID</th>
                    <th style={{ padding: '8px 10px' }}>PROVIDER</th>
                    <th style={{ padding: '8px 10px' }}>LABEL</th>
                    <th style={{ padding: '8px 10px' }}>MASKED SAMPLE CONTENT</th>
                    <th style={{ padding: '8px 10px' }}>NOTES / DESCRIPTION</th>
                    <th style={{ padding: '8px 10px' }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {samplesLoading ? (
                    <tr>
                      <td colSpan="6" style={{ padding: '30px', textAlign: 'center', color: '#19D3FF' }}>
                        <RefreshCw size={24} className="spin-icon" style={{ margin: '0 auto 8px auto' }} />
                        <div>Loading masked samples...</div>
                      </td>
                    </tr>
                  ) : samples.map(s => (
                    <tr key={s.sample_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#38BDF8' }}>{s.sample_id}</td>
                      <td style={{ padding: '8px 10px', textTransform: 'uppercase', color: '#E8F1FF', fontWeight: 600 }}>{s.provider}</td>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          background: s.label === 'positive' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                          color: s.label === 'positive' ? '#4ADE80' : '#94A3B8'
                        }}>
                          {s.label.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#CBD5E1', maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {s.masked_sample}
                      </td>
                      <td style={{ padding: '8px 10px', color: '#8AA4C8', fontSize: '0.78rem' }}>{s.notes}</td>
                      <td style={{ padding: '8px 10px' }}>
                        <button
                          onClick={() => {
                            setSingleProvider(s.provider);
                            setSingleLabel(s.label);
                            setActiveTab('single_test');
                            handleRunSingleTest();
                          }}
                          style={{
                            background: 'rgba(25, 211, 255, 0.15)',
                            border: '1px solid rgba(25, 211, 255, 0.35)',
                            color: '#19D3FF',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            cursor: 'pointer'
                          }}
                        >
                          Test in Mode A
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
              <span style={{ color: '#8AA4C8', fontSize: '0.8rem' }}>
                Page {samplesPage + 1} of {Math.ceil(samplesTotal / samplesLimit) || 1}
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => setSamplesPage(Math.max(0, samplesPage - 1))}
                  disabled={samplesPage === 0 || samplesLoading}
                  style={pageBtnStyle(samplesPage === 0 || samplesLoading)}
                >
                  Previous
                </button>
                <button
                  onClick={() => setSamplesPage(samplesPage + 1)}
                  disabled={(samplesPage + 1) * samplesLimit >= samplesTotal || samplesLoading}
                  style={pageBtnStyle((samplesPage + 1) * samplesLimit >= samplesTotal || samplesLoading)}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: DATASET STATISTICS & LICENSING */}
      {/* ========================================================================= */}
      {activeTab === 'stats' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 360px), 1fr))', gap: '20px', width: '100%', boxSizing: 'border-box' }}>
          {/* Generation Provenance */}
          <div style={boxCardStyle}>
            <h3 style={{ margin: '0 0 14px 0', fontSize: '1.05rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={18} color="#00E5FF" />
              <span>Dataset Provenance (10,000 Samples)</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Total Balanced Samples:</span>
                <strong style={{ color: '#E8F1FF' }}>10,000</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Positive Samples (Real Signatures):</span>
                <strong style={{ color: '#4ADE80' }}>5,000 (50.0%)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Negative Samples (Lookalikes/Dummies):</span>
                <strong style={{ color: '#F87171' }}>5,000 (50.0%)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Custom Synthetic Engine Samples:</span>
                <strong style={{ color: '#38BDF8' }}>9,994 (99.94%)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Nightfall AI Attribution Reference:</span>
                <strong style={{ color: '#FBBF24' }}>6 quarantined reference samples</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Provider Coverage Count:</span>
                <strong style={{ color: '#00E5FF' }}>10 Target Providers</strong>
              </div>
            </div>
          </div>

          {/* Stratified Splits */}
          <div style={boxCardStyle}>
            <h3 style={{ margin: '0 0 14px 0', fontSize: '1.05rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#38BDF8" />
              <span>Stratified Split Allocations (Seed 42)</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Training Split (70%):</span>
                <strong style={{ color: '#38BDF8' }}>7,000 samples (3,500 pos / 3,500 neg)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Validation Split (15%):</span>
                <strong style={{ color: '#C084FC' }}>1,500 samples (750 pos / 750 neg)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Held-Out Test Split (15%):</span>
                <strong style={{ color: '#00E5FF' }}>1,500 samples (750 pos / 750 neg)</strong>
              </div>
              <div style={rowStyle}>
                <span style={{ color: '#8AA4C8' }}>Leakage Prevention:</span>
                <strong style={{ color: '#22C55E' }}>Verified Zero Overlap across Hashes</strong>
              </div>
            </div>
          </div>

          {/* Licensing & Compliance */}
          <div style={{ ...boxCardStyle, gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 14px 0', fontSize: '1.05rem', color: '#E8F1FF', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} color="#C084FC" />
              <span>Attribution, Licensing &amp; Quarantine Governance</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.84rem', color: '#8AA4C8', lineHeight: 1.6 }}>
              <div>
                <strong style={{ color: '#E8F1FF' }}>Nightfall AI Sample Data:</strong> Attributed to Nightfall Policy Templates (<a href="https://help.nightfall.ai/nightfall_policy_templates/sample_data" target="_blank" rel="noreferrer" style={{ color: '#19D3FF' }}>help.nightfall.ai</a>). Used for DLP and secret evaluation. Upstream active tokens quarantined and excluded from raw distribution.
              </div>
              <div>
                <strong style={{ color: '#E8F1FF' }}>GitHub Supported Secret Scanning Patterns:</strong> Attributed to GitHub Secret Scanning Partner Documentation (<a href="https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns" target="_blank" rel="noreferrer" style={{ color: '#19D3FF' }}>docs.github.com</a>). Documented patterns used strictly as format reference.
              </div>
              <div>
                <strong style={{ color: '#E8F1FF' }}>Zero-Live-Credential Enforcement:</strong> API Sentinel enforces a zero-live-credential policy. All synthetic keys are generated using deterministic pseudo-random sequences and are structurally nonfunctional. No outbound authentication or live token probing is permitted.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const kpiCardStyle = {
  background: 'linear-gradient(135deg, #07182B 0%, #0D2744 100%)',
  border: '1px solid rgba(25, 211, 255, 0.2)',
  borderRadius: '12px',
  padding: '18px 20px',
  boxShadow: '0 4px 16px rgba(0, 10, 25, 0.3)',
};

const boxCardStyle = {
  background: 'linear-gradient(135deg, #07182B 0%, #0A1F38 100%)',
  border: '1px solid rgba(25, 211, 255, 0.18)',
  borderRadius: '12px',
  padding: '20px',
  boxShadow: '0 4px 16px rgba(0, 10, 25, 0.3)',
};

const selectStyle = {
  background: '#050D1F',
  border: '1px solid rgba(25, 211, 255, 0.3)',
  borderRadius: '6px',
  color: '#E8F1FF',
  padding: '6px 12px',
  fontSize: '0.84rem',
  cursor: 'pointer'
};

const rowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  padding: '4px 0',
  borderBottom: '1px solid rgba(255, 255, 255, 0.04)'
};

const pageBtnStyle = (disabled) => ({
  background: disabled ? 'rgba(255, 255, 255, 0.05)' : 'rgba(25, 211, 255, 0.15)',
  border: `1px solid ${disabled ? 'rgba(255, 255, 255, 0.1)' : 'rgba(25, 211, 255, 0.4)'}`,
  color: disabled ? '#475569' : '#19D3FF',
  padding: '6px 14px',
  borderRadius: '6px',
  fontSize: '0.8rem',
  fontWeight: 600,
  cursor: disabled ? 'not-allowed' : 'pointer'
});
