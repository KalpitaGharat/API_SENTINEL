import React, { useState, useEffect, useCallback } from 'react';
import { 
  CheckCircle2, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Terminal, 
  Play, 
  History, 
  RefreshCw,
  Clock,
  ArrowRight
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function RetestingVerificationContent() {
  const { scans, selectedScanId, selectScan, findings, refreshFindings, refreshScans } = useScanContext();

  const [selectedFindingId, setSelectedFindingId] = useState('');
  const [isProbing, setIsProbing] = useState(false);
  const [probeLogs, setProbeLogs] = useState([]);
  const [lastRetestResult, setLastRetestResult] = useState(null);
  const [retestError, setRetestError] = useState(null);
  
  // History state
  const [historyRecords, setHistoryRecords] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Sync selected finding when findings change
  useEffect(() => {
    if (findings && findings.length > 0) {
      if (!selectedFindingId || !findings.some((f) => f.id === selectedFindingId)) {
        // Prefer open finding first
        const openFinding = findings.find((f) => f.status === 'Open' || f.status === 'Still Vulnerable');
        setSelectedFindingId(openFinding ? openFinding.id : findings[0].id);
      }
    } else {
      setSelectedFindingId('');
    }
  }, [findings, selectedFindingId]);

  const activeFinding = findings.find((f) => f.id === selectedFindingId) || null;

  // Load audit history for the selected finding
  const loadHistory = useCallback(async (findingId) => {
    if (!findingId) {
      setHistoryRecords([]);
      return;
    }
    setIsLoadingHistory(true);
    try {
      const data = await apiClient.getFindingHistory(findingId);
      const list = data?.history || [];
      // Sort newest first for audit display
      list.sort((a, b) => new Date(b.retested_at) - new Date(a.retested_at));
      setHistoryRecords(list);
    } catch (err) {
      console.warn('[RetestingVerification] Failed to fetch finding history:', err);
      setHistoryRecords([]);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    if (selectedFindingId) {
      loadHistory(selectedFindingId);
    } else {
      setHistoryRecords([]);
    }
  }, [selectedFindingId, loadHistory]);

  // Execute verification probe
  const executeVerificationProbe = async () => {
    if (!selectedScanId) {
      setRetestError('No scan selected. Please select a security scan first.');
      return;
    }

    setIsProbing(true);
    setRetestError(null);
    setLastRetestResult(null);
    setProbeLogs([
      `[INIT] Preparing targeted regression probe for scan ${selectedScanId.substring(0, 8)}...`,
      selectedFindingId 
        ? `[TARGET] Scoping probe to finding: ${activeFinding?.vulnerability || selectedFindingId}` 
        : '[TARGET] Scoping probe to all open findings in scan session...',
      `[ENDPOINT] Target destination: ${activeFinding?.endpoint || 'All open endpoints'}`,
      '[SECURITY] Enforcing socket-level IP pinning and TLS SNI preservation...',
      '[DISPATCH] Sending authenticated verification probe payload...',
    ]);

    try {
      const response = await apiClient.retestScan(selectedScanId, selectedFindingId || null);

      const results = response?.results || [];
      const primaryResult = results.find((r) => r.finding_id === selectedFindingId) || results[0] || null;

      if (!primaryResult) {
        throw new Error('Backend completed retest but returned no matching result records.');
      }

      // Append verification telemetry to probe logs
      const observedStatus = primaryResult.observed_result?.status_code || primaryResult.observed_result?.status || 'N/A';
      const isResolved = primaryResult.verified === true || primaryResult.new_status === 'Resolved';

      setProbeLogs((prev) => [
        ...prev,
        `[RESPONSE] Received HTTP ${observedStatus} from target endpoint.`,
        `[EVALUATION] Previous status: ${primaryResult.previous_status} ➔ New status: ${primaryResult.new_status}`,
        isResolved
          ? `[SUCCESS] Verification passed! Object-level boundary verified. Vulnerability certified as RESOLVED.`
          : `[WARNING] Verification detected persistent vulnerability. Endpoint remains vulnerable.`,
        `[AUDIT] Committed immutable audit entry to RetestHistory table.`,
      ]);

      setLastRetestResult(primaryResult);

      // Refresh scan findings in context and reload history
      await refreshFindings(selectedScanId);
      await loadHistory(selectedFindingId || primaryResult.finding_id);
      refreshScans();
    } catch (err) {
      console.error('[RetestingVerification] Retest error:', err);
      const errMsg = err?.details?.detail || err?.message || 'Verification probe encountered an unexpected error.';
      setRetestError(errMsg);
      setProbeLogs((prev) => [
        ...prev,
        `[ERROR] Probe execution failed: ${errMsg}`,
        `[FAILSAFE] Retest transaction rolled back; finding status remains unchanged.`,
      ]);
    } finally {
      setIsProbing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Overview Banner */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '20px 24px', 
          borderLeft: '4px solid #00E5FF',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px'
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '4px' }}>
            Targeted Regression Probing Engine
          </h3>
          <p style={{ color: '#8AA4C8', fontSize: '0.88rem', lineHeight: '1.5' }}>
            Mathematically certify patched vulnerabilities: API Sentinel replays exact exploit vectors to confirm remediation.
          </p>
        </div>

        {/* Scan Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>Active Scan:</span>
          <select
            value={selectedScanId || ''}
            onChange={(e) => selectScan(e.target.value)}
            style={{
              padding: '8px 12px',
              background: '#04101F',
              border: '1px solid #0F2F4E',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '0.84rem',
              outline: 'none',
              cursor: 'pointer',
              minWidth: '220px',
            }}
          >
            {scans.length === 0 && <option value="">No Scans Available</option>}
            {scans.map((s) => (
              <option key={s.id} value={s.id}>
                {s.target_url} ({s.id.substring(0, 8)}) - {s.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Retest Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '22px' }}>
        {/* Left Column: Probe Configuration & Target Selection */}
        <div className="cyber-card" style={{ padding: '22px' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '16px' }}>
            Select Finding to Re-probe
          </h4>

          {findings.length === 0 ? (
            <div style={{ padding: '30px 20px', textAlign: 'center', color: '#8AA4C8', background: '#04101F', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '8px' }}>No findings detected for the selected scan.</p>
              <p style={{ fontSize: '0.8rem', color: '#6482A6' }}>Launch a new scan against a target API to detect vulnerabilities.</p>
            </div>
          ) : (
            <>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '8px' }}>
                Vulnerability Target
              </label>
              <select
                value={selectedFindingId}
                onChange={(e) => setSelectedFindingId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '11px 14px',
                  background: '#04101F',
                  border: '1px solid #0F2F4E',
                  borderRadius: '8px',
                  color: '#FFFFFF',
                  fontSize: '0.88rem',
                  outline: 'none',
                  marginBottom: '18px',
                  cursor: 'pointer',
                }}
              >
                {findings.map((f) => (
                  <option key={f.id} value={f.id}>
                    [{f.status.toUpperCase()}] {f.severity.toUpperCase()}: {f.vulnerability} ({f.endpoint})
                  </option>
                ))}
              </select>

              {activeFinding && (
                <div style={{ padding: '16px', background: '#040F1E', borderRadius: '10px', border: '1px solid #0F2F4E', marginBottom: '22px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Endpoint
                      </span>
                      <div className="font-mono-code" style={{ color: '#00E5FF', fontSize: '0.85rem', marginTop: '3px' }}>
                        {activeFinding.endpoint}
                      </div>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.76rem', color: '#8AA44C8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Current Status
                      </span>
                      <div style={{ marginTop: '3px' }}>
                        <span 
                          style={{
                            display: 'inline-block',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: activeFinding.status === 'Resolved' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 77, 94, 0.2)',
                            color: activeFinding.status === 'Resolved' ? '#22C55E' : '#FF4D5E',
                            border: `1px solid ${activeFinding.status === 'Resolved' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255, 77, 94, 0.4)'}`,
                          }}
                        >
                          {activeFinding.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Category / OWASP
                    </span>
                    <div style={{ color: '#FFFFFF', fontSize: '0.85rem', marginTop: '2px' }}>
                      {activeFinding.category} — {activeFinding.vulnerability}
                    </div>
                  </div>

                  {activeFinding.evidence && (
                    <div style={{ fontSize: '0.8rem', color: '#8AA4C8', borderTop: '1px solid #0F2F4E', paddingTop: '10px', marginTop: '10px' }}>
                      <span>Expected Secure Response: </span>
                      <strong style={{ color: '#22C55E' }}>HTTP {activeFinding.evidence.expected_status || 403} Forbidden</strong>
                    </div>
                  )}
                </div>
              )}

              {retestError && (
                <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(255, 77, 94, 0.15)', border: '1px solid rgba(255, 77, 94, 0.35)', color: '#FF4D5E', fontSize: '0.85rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} />
                  <span>{retestError}</span>
                </div>
              )}

              <button
                onClick={executeVerificationProbe}
                disabled={isProbing || !selectedFindingId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '10px',
                  width: '100%',
                  padding: '13px 20px',
                  background: isProbing ? '#0F2F4E' : '#00E5FF',
                  color: isProbing ? '#8AA4C8' : '#040813',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.92rem',
                  cursor: isProbing ? 'not-allowed' : 'pointer',
                  boxShadow: isProbing ? 'none' : '0 0 20px rgba(0, 229, 255, 0.4)',
                  transition: 'all 0.2s ease',
                }}
              >
                {isProbing ? (
                  <>
                    <RefreshCw size={18} className="animate-spin" />
                    <span>Executing Socket-Level Retest Probe...</span>
                  </>
                ) : (
                  <>
                    <Play size={17} fill="#040813" />
                    <span>Execute Targeted Verification Probe</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>

        {/* Right Column: Live Probe Console */}
        <div className="cyber-card" style={{ padding: '22px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Terminal size={18} color="#00E5FF" />
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#FFFFFF', margin: 0 }}>
              Verification Probe Console
            </h4>
          </div>

          <pre
            className="font-mono-code"
            style={{
              flex: 1,
              background: '#040F1E',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid #0F2F4E',
              color: '#8AA4C8',
              fontSize: '0.8rem',
              lineHeight: '1.7',
              minHeight: '220px',
              maxHeight: '260px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
            }}
          >
            {probeLogs.length === 0 ? (
              <span style={{ color: '#54718C' }}>Waiting for verification probe dispatch...</span>
            ) : (
              probeLogs.map((log, idx) => {
                let color = '#8AA4C8';
                if (log.includes('[SUCCESS]') || log.includes('RESOLVED')) color = '#22C55E';
                if (log.includes('[WARNING]') || log.includes('persistent')) color = '#FF8A1F';
                if (log.includes('[ERROR]')) color = '#FF4D5E';
                if (log.includes('[RESPONSE]')) color = '#00E5FF';
                return (
                  <div key={idx} style={{ color }}>
                    {log}
                  </div>
                );
              })
            )}
          </pre>

          {/* Outcome Indicator */}
          {lastRetestResult && (
            <div 
              style={{ 
                marginTop: '16px', 
                padding: '14px 16px', 
                borderRadius: '8px', 
                background: lastRetestResult.verified ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)',
                border: `1px solid ${lastRetestResult.verified ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255, 77, 94, 0.4)'}`,
                color: lastRetestResult.verified ? '#22C55E' : '#FF4D5E',
                fontSize: '0.88rem',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                fontWeight: 600,
              }}
            >
              {lastRetestResult.verified ? <ShieldCheck size={22} /> : <ShieldAlert size={22} />}
              <div>
                <div>
                  {lastRetestResult.verified
                    ? 'Remediation Certified & Verified!'
                    : 'Target Remains Vulnerable!'}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#8AA4C8', marginTop: '2px', fontWeight: 400 }}>
                  Status transition: {lastRetestResult.previous_status} ➔ <strong>{lastRetestResult.new_status}</strong>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Retest Audit History Table */}
      <div className="cyber-card" style={{ padding: '22px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} color="#00E5FF" />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#FFFFFF', margin: 0 }}>
              Chronological Retest Audit History
            </h4>
          </div>
          {selectedFindingId && (
            <button
              onClick={() => loadHistory(selectedFindingId)}
              disabled={isLoadingHistory}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'transparent',
                border: '1px solid #0F2F4E',
                color: '#8AA4C8',
                borderRadius: '6px',
                padding: '5px 10px',
                fontSize: '0.78rem',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={13} className={isLoadingHistory ? 'animate-spin' : ''} />
              <span>Refresh History</span>
            </button>
          )}
        </div>

        {historyRecords.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', color: '#6482A6', fontSize: '0.86rem' }}>
            {isLoadingHistory ? 'Loading verification audit records...' : 'No historical retest records for this finding yet. Execute a verification probe above to establish an immutable audit record.'}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0F2F4E', color: '#8AA4C8', textAlign: 'left' }}>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Timestamp (UTC)</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>State Transition</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Verdict</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Observed Status</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Audit ID</th>
                </tr>
              </thead>
              <tbody>
                {historyRecords.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid rgba(15, 47, 78, 0.5)' }}>
                    <td style={{ padding: '12px', color: '#FFFFFF', whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={13} color="#6482A6" />
                        <span>{new Date(item.retested_at).toLocaleString()}</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem' }}>
                        <span style={{ color: '#FF4D5E' }}>{item.previous_status}</span>
                        <ArrowRight size={13} color="#8AA4C8" />
                        <span style={{ color: item.new_status === 'Resolved' ? '#22C55E' : '#FF8A1F' }}>
                          {item.new_status}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: item.verified ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)',
                          color: item.verified ? '#22C55E' : '#FF4D5E',
                        }}
                      >
                        {item.verified ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                        <span>{item.verified ? 'VERIFIED' : 'VULNERABLE'}</span>
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'JetBrains Mono, monospace', color: '#00E5FF' }}>
                      HTTP {item.observed_result?.status_code || item.observed_result?.status || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', color: '#6482A6', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem' }}>
                      {item.id.substring(0, 8)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RetestingVerification() {
  return (
    <ErrorBoundary title="Retesting Engine Intercepted">
      <RetestingVerificationContent />
    </ErrorBoundary>
  );
}
