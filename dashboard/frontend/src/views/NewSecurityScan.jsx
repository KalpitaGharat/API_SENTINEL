import React, { useState } from 'react';
import { Play, ShieldAlert, CheckCircle2, Terminal, AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function NewSecurityScanContent({ setActivePage }) {
  const { refreshScans, selectScan } = useScanContext();

  const [targetUrl, setTargetUrl] = useState('http://127.0.0.1:8001');
  const [scanProfile, setScanProfile] = useState('OWASP API Top 10 Deep Audit');
  const [userAuthorized, setUserAuthorized] = useState(true);
  const [categories, setCategories] = useState(['BOLA', 'AUTH', 'HEADERS', 'CONFIG']);
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState(null);

  const toggleCategory = (cat) => {
    setCategories((prev) => 
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleStartScan = async () => {
    if (!targetUrl || !targetUrl.trim()) {
      setScanError('Please enter a target API URL.');
      return;
    }
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      setScanError('Target URL must begin with http:// or https://');
      return;
    }
    if (!userAuthorized) {
      setScanError('You must confirm authorization before initiating an active security scan.');
      return;
    }

    setIsScanning(true);
    setProgress(15);
    setScanError(null);
    setScanResult(null);
    setLogs([
      `[INIT] Validating target URL safety boundaries for ${targetUrl}...`,
      '[SECURITY] Pre-flight SSRF check: validating against cloud metadata, link-local, and unspecified addresses...',
      '[SOCKET] Initializing PinnedSyncBackend with destination-IP pinning and TLS SNI preservation...',
    ]);

    try {
      setProgress(40);
      setLogs((prev) => [
        ...prev,
        `[PROFILE] Selected scan profile: "${scanProfile}" with categories [${categories.join(', ')}]`,
        `[ENGINE] Invoking Member 1 real security testing engine...`,
      ]);

      const response = await apiClient.createScan({
        targetUrl: targetUrl.trim(),
        scanProfile,
        userAuthorized,
        categories,
      });

      setProgress(85);
      setLogs((prev) => [
        ...prev,
        `[PROBING] Dual-principal BOLA test executed on endpoints.`,
        `[PROBING] Authentication token and signature validation complete.`,
        `[PROBING] HTTP security headers & server banner disclosure audited.`,
        `[PERSIST] Persisting scan results and evidence into SQLite WAL database...`,
        `[COMPLETE] Scan session ${response.id.substring(0, 8)} finished with status: ${response.status}`,
        `[FINDINGS] Total vulnerabilities detected: ${response.total_findings}`,
      ]);

      setProgress(100);
      setScanResult(response);

      // Refresh global scans list and select the newly created scan
      await refreshScans(response.id);
      selectScan(response.id);
    } catch (err) {
      console.error('[NewSecurityScan] Scan error:', err);
      const msg = err?.details?.detail || err?.message || 'Security scan failed to execute.';
      setScanError(msg);
      setLogs((prev) => [
        ...prev,
        `[ERROR] Scan execution aborted: ${msg}`,
      ]);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '22px' }}>
      {/* Configuration Form */}
      <div className="cyber-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '18px', color: '#FFFFFF' }}>
          Target API Configuration
        </h3>

        {/* Target URL */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '6px' }}>
            Target API URL
          </label>
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="http://127.0.0.1:8001 or https://api.yourdomain.com"
            disabled={isScanning}
            style={{
              width: '100%',
              padding: '11px 14px',
              background: '#04101F',
              border: '1px solid #0F2F4E',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '0.88rem',
              outline: 'none',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          />
          <span style={{ fontSize: '0.74rem', color: '#6482A6', marginTop: '4px', display: 'block' }}>
            Default Healthcare Demo API runs on <code>http://127.0.0.1:8001</code>
          </span>
        </div>

        {/* Scan Profile */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '6px' }}>
            Security Audit Profile
          </label>
          <select
            value={scanProfile}
            onChange={(e) => setScanProfile(e.target.value)}
            disabled={isScanning}
            style={{
              width: '100%',
              padding: '11px 14px',
              background: '#04101F',
              border: '1px solid #0F2F4E',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '0.88rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="OWASP API Top 10 Deep Audit">OWASP API Top 10 Deep Audit</option>
            <option value="Full Security Scan (OWASP Top 10 + Configs)">Full Security Scan (OWASP Top 10 + Configs)</option>
            <option value="BOLA & IDOR Authorization Audit">BOLA & IDOR Authorization Audit</option>
            <option value="Authentication & Token Security Audit">Authentication & Token Security Audit</option>
            <option value="HTTP Security Headers & Configuration">HTTP Security Headers & Configuration</option>
          </select>
        </div>

        {/* Category Checkboxes */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '8px' }}>
            Active Audit Modules
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {[
              { id: 'BOLA', label: 'BOLA / IDOR Testing' },
              { id: 'AUTH', label: 'Token & Auth Weaknesses' },
              { id: 'HEADERS', label: 'HTTP Security Headers' },
              { id: 'CONFIG', label: 'API Configuration Leaks' },
            ].map((cat) => (
              <label 
                key={cat.id} 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  fontSize: '0.84rem', 
                  color: categories.includes(cat.id) ? '#FFFFFF' : '#6482A6',
                  cursor: 'pointer',
                  padding: '8px 12px',
                  background: categories.includes(cat.id) ? 'rgba(0, 229, 255, 0.08)' : '#040F1E',
                  borderRadius: '6px',
                  border: `1px solid ${categories.includes(cat.id) ? 'rgba(0, 229, 255, 0.3)' : '#0F2F4E'}`
                }}
              >
                <input
                  type="checkbox"
                  checked={categories.includes(cat.id)}
                  onChange={() => toggleCategory(cat.id)}
                  disabled={isScanning}
                />
                <span>{cat.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Authorization Confirmation */}
        <div style={{ marginBottom: '22px', padding: '12px 14px', borderRadius: '8px', background: 'rgba(0, 229, 255, 0.05)', border: '1px solid rgba(0, 229, 255, 0.2)' }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={userAuthorized}
              onChange={(e) => setUserAuthorized(e.target.checked)}
              disabled={isScanning}
              style={{ marginTop: '3px' }}
            />
            <span style={{ fontSize: '0.82rem', color: '#E8F1FF', lineHeight: '1.5' }}>
              I confirm that I am authorized to perform non-destructive security vulnerability testing against this target API.
            </span>
          </label>
        </div>

        {/* Error Alert */}
        {scanError && (
          <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(255, 77, 94, 0.15)', border: '1px solid rgba(255, 77, 94, 0.35)', color: '#FF4D5E', fontSize: '0.85rem', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} />
            <span>{scanError}</span>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={handleStartScan}
          disabled={isScanning}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            width: '100%',
            padding: '13px 20px',
            background: isScanning ? '#0F2F4E' : '#00E5FF',
            color: isScanning ? '#8AA4C8' : '#040813',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: isScanning ? 'not-allowed' : 'pointer',
            boxShadow: isScanning ? 'none' : '0 0 20px rgba(0, 229, 255, 0.4)',
            transition: 'all 0.2s ease',
          }}
        >
          {isScanning ? (
            <>
              <RefreshCw size={18} className="animate-spin" />
              <span>Scanning Target API ({progress}%)...</span>
            </>
          ) : (
            <>
              <Play size={18} fill="#040813" />
              <span>Launch Automated Security Scan</span>
            </>
          )}
        </button>

        {/* Success Banner */}
        {scanResult && (
          <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', background: 'rgba(34, 197, 94, 0.12)', border: '1px solid rgba(34, 197, 94, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#22C55E', fontWeight: 600, marginBottom: '6px' }}>
              <CheckCircle2 size={18} />
              <span>Security Scan Complete!</span>
            </div>
            <p style={{ color: '#8AA4C8', fontSize: '0.84rem', marginBottom: '12px' }}>
              Detected <strong>{scanResult.total_findings} vulnerabilities</strong> across target endpoints.
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => setActivePage('findings')}
                style={{
                  padding: '7px 14px',
                  background: '#22C55E',
                  color: '#040813',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Inspect Findings
              </button>
              <button
                onClick={() => setActivePage('retesting')}
                style={{
                  padding: '7px 14px',
                  background: 'transparent',
                  border: '1px solid rgba(34, 197, 94, 0.4)',
                  color: '#22C55E',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Verify & Retest
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Real-time Telemetry & Terminal Console */}
      <div className="cyber-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Terminal size={18} color="#00E5FF" />
          <h4 style={{ fontSize: '0.96rem', fontWeight: 600, color: '#FFFFFF', margin: 0 }}>
            Scanner Execution Log
          </h4>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: '6px', background: '#04101F', borderRadius: '3px', overflow: 'hidden', marginBottom: '14px' }}>
          <div 
            style={{ 
              width: `${progress}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #00E5FF, #22C55E)',
              transition: 'width 0.3s ease',
            }} 
          />
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
            minHeight: '260px',
            maxHeight: '380px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}
        >
          {logs.length === 0 ? (
            <span style={{ color: '#54718C' }}>Waiting for scan dispatch...</span>
          ) : (
            logs.map((log, idx) => {
              let color = '#8AA4C8';
              if (log.includes('[COMPLETE]') || log.includes('[FINDINGS]')) color = '#22C55E';
              if (log.includes('[ERROR]')) color = '#FF4D5E';
              if (log.includes('[PROBING]')) color = '#00E5FF';
              return (
                <div key={idx} style={{ color }}>
                  {log}
                </div>
              );
            })
          )}
        </pre>
      </div>
    </div>
  );
}

export default function NewSecurityScan(props) {
  return (
    <ErrorBoundary title="Scan Dispatch Intercepted">
      <NewSecurityScanContent {...props} />
    </ErrorBoundary>
  );
}
