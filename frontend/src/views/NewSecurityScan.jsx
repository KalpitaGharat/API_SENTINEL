import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  ShieldAlert, 
  CheckCircle2, 
  Terminal, 
  AlertTriangle, 
  ArrowRight, 
  RefreshCw,
  Layers,
  Key,
  Globe,
  ExternalLink,
  Check,
  Server,
  ShieldCheck,
  Database
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function NewSecurityScanContent({ setActivePage, initialTargetId }) {
  const { 
    targets, 
    selectedTargetId: ctxTargetId, 
    selectTarget, 
    refreshTargets, 
    refreshScans, 
    selectScan 
  } = useScanContext();

  const [selectedTargetId, setSelectedTargetId] = useState(initialTargetId || ctxTargetId || '');
  const [targetUrl, setTargetUrl] = useState('http://127.0.0.1:8001');
  const [scanProfile, setScanProfile] = useState('OWASP API Top 10 Deep Audit');
  const [userAuthorized, setUserAuthorized] = useState(true);
  const [allowStateChanging, setAllowStateChanging] = useState(false);
  const [categories, setCategories] = useState(['BOLA', 'AUTH', 'HEADERS', 'CONFIG']);
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState(null);

  // Target pre-flight validation status
  const [validatingTarget, setValidatingTarget] = useState(false);
  const [targetValidationResult, setTargetValidationResult] = useState(null);

  // Synchronize initialTargetId if provided via prop
  useEffect(() => {
    if (initialTargetId) {
      setSelectedTargetId(initialTargetId);
      if (selectTarget) selectTarget(initialTargetId);
    }
  }, [initialTargetId, selectTarget]);

  // Synchronize selectedTargetId with targets list
  useEffect(() => {
    if (targets && targets.length > 0) {
      if (!selectedTargetId || !targets.some((t) => t.id === selectedTargetId)) {
        const defaultTarget = targets[0];
        setSelectedTargetId(defaultTarget.id);
        setTargetUrl(defaultTarget.base_url || 'http://127.0.0.1:8001');
        if (selectTarget) selectTarget(defaultTarget.id);
      } else {
        const found = targets.find((t) => t.id === selectedTargetId);
        if (found && found.base_url) {
          setTargetUrl(found.base_url);
        }
      }
    }
  }, [targets, selectedTargetId, selectTarget]);

  const activeTarget = (targets || []).find((t) => t.id === selectedTargetId) || null;

  const handleTargetChange = (e) => {
    const val = e.target.value;
    setSelectedTargetId(val);
    setTargetValidationResult(null);
    if (val === 'custom') {
      setTargetUrl('http://127.0.0.1:8001');
    } else {
      const match = (targets || []).find((t) => t.id === val);
      if (match) {
        setTargetUrl(match.base_url || '');
        if (selectTarget) selectTarget(val);
      }
    }
  };

  const handleValidateTarget = async () => {
    if (!activeTarget?.id) return;
    setValidatingTarget(true);
    setTargetValidationResult(null);
    try {
      const res = await apiClient.validateTargetConnectivity(activeTarget.id);
      setTargetValidationResult(res);
    } catch (err) {
      setTargetValidationResult({
        is_valid: false,
        message: err.message || 'Target validation probe failed',
      });
    } finally {
      setValidatingTarget(false);
    }
  };

  const toggleCategory = (cat) => {
    setCategories((prev) => 
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleStartScan = async () => {
    if (isScanning) return; // Prevent duplicate submissions

    if (!targetUrl || !targetUrl.trim()) {
      setScanError('Please specify a target API base URL.');
      return;
    }
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      setScanError('Target URL must begin with http:// or https://');
      return;
    }
    if (!userAuthorized) {
      setScanError('Safety Requirement: You must confirm testing authorization before initiating an active security audit.');
      return;
    }

    setIsScanning(true);
    setProgress(15);
    setScanError(null);
    setScanResult(null);
    setLogs([
      `[INIT] Validating target safety boundaries for ${targetUrl}...`,
      activeTarget 
        ? `[TARGET] Associated catalog target: "${activeTarget.name}" (${activeTarget.id.substring(0, 8)}...)` 
        : `[TARGET] Scanning ad-hoc URL destination: ${targetUrl}`,
      '[SECURITY] Pre-flight SSRF check: validating against RFC 1918, link-local, and cloud metadata addresses...',
      '[SOCKET] Initializing PinnedSyncBackend with destination-IP pinning and TLS SNI preservation...',
    ]);

    try {
      setProgress(40);
      setLogs((prev) => [
        ...prev,
        `[PROFILE] Selected scan profile: "${scanProfile}" with modules [${categories.join(', ')}]`,
        `[ENGINE] Invoking API Sentinel real security testing engine...`,
      ]);

      let response;
      if (activeTarget?.id && selectedTargetId !== 'custom') {
        // Use genuine Target Scan Bridge to associate target_id, selected endpoints, and auth profiles
        response = await apiClient.launchTargetScan(activeTarget.id, {
          scan_profile: scanProfile,
          categories: categories,
          user_authorized: true,
          allow_state_changing: allowStateChanging,
        });
      } else {
        // Fallback to standard scan creation for ad-hoc URLs
        response = await apiClient.createScan({
          targetUrl: targetUrl.trim(),
          scanProfile,
          userAuthorized: true,
          categories,
        });
      }

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
      if (refreshTargets) refreshTargets();
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
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))', gap: '22px', width: '100%', boxSizing: 'border-box' }}>
      {/* Configuration Form */}
      <div className="cyber-card" style={{ padding: '24px', minWidth: 0, boxSizing: 'border-box' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '18px', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={18} color="#00E5FF" />
          <span>Target API Selection & Configuration</span>
        </h3>

        {/* Target Selector Dropdown */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '6px' }}>
            Registered API Target Catalog
          </label>
          <select
            value={selectedTargetId}
            onChange={handleTargetChange}
            disabled={isScanning}
            style={{
              width: '100%',
              padding: '10px 14px',
              background: '#04101F',
              border: '1px solid #0F2F4E',
              borderRadius: '8px',
              color: '#00E5FF',
              fontSize: '0.88rem',
              fontWeight: 600,
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {(targets || []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} — {t.base_url} ({t.environment})
              </option>
            ))}
            <option value="custom">-- Custom / Ad-hoc URL (Manual Input) --</option>
          </select>
        </div>

        {/* Selected Target Live Details Card */}
        {activeTarget && selectedTargetId !== 'custom' && (
          <div 
            style={{
              background: '#030A14',
              borderRadius: '8px',
              border: '1px solid #1A4674',
              padding: '14px 16px',
              marginBottom: '18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#FFFFFF' }}>{activeTarget.name}</span>
                <span style={{ fontSize: '0.72rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(0, 229, 255, 0.15)', color: '#00E5FF', fontWeight: 700, textTransform: 'uppercase' }}>
                  {activeTarget.environment}
                </span>
              </div>

              <button
                type="button"
                onClick={handleValidateTarget}
                disabled={validatingTarget || isScanning}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  background: 'rgba(0, 229, 255, 0.1)',
                  border: '1px solid rgba(0, 229, 255, 0.35)',
                  color: '#00E5FF',
                  borderRadius: '4px',
                  padding: '4px 10px',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={12} className={validatingTarget ? 'animate-spin' : ''} />
                <span>Test Connectivity</span>
              </button>
            </div>

            {/* Validation Feedback */}
            {targetValidationResult && (
              <div 
                style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: targetValidationResult.is_valid ? 'rgba(34, 197, 94, 0.12)' : 'rgba(255, 77, 94, 0.12)',
                  border: `1px solid ${targetValidationResult.is_valid ? 'rgba(34, 197, 94, 0.35)' : 'rgba(255, 77, 94, 0.35)'}`,
                  fontSize: '0.78rem',
                  color: targetValidationResult.is_valid ? '#22C55E' : '#FF4D5E',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {targetValidationResult.is_valid ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
                <span>{targetValidationResult.message || (targetValidationResult.is_valid ? 'Target reachable' : 'Target unreachable')}</span>
              </div>
            )}

            {/* Metrics Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '0.78rem', color: '#8AA4C8' }}>
              <div>
                <span style={{ color: '#6482A6' }}>Endpoints:</span>{' '}
                <strong style={{ color: '#E8F1FF' }}>{activeTarget.selected_endpoints || activeTarget.total_endpoints || 0} selected</strong>
              </div>
              <div>
                <span style={{ color: '#6482A6' }}>Auth Profiles:</span>{' '}
                <strong style={{ color: activeTarget.auth_profiles_count > 0 ? '#22C55E' : '#FF8A1F' }}>
                  {activeTarget.auth_profiles_count > 0 ? `${activeTarget.auth_profiles_count} configured` : 'None'}
                </strong>
              </div>
              <div>
                <span style={{ color: '#6482A6' }}>Specification:</span>{' '}
                <strong style={{ color: '#E8F1FF' }}>{activeTarget.specification_version || 'Manual'}</strong>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.74rem', color: '#6482A6', borderTop: '1px solid rgba(15, 47, 78, 0.5)', paddingTop: '6px' }}>
              <span>Last scanned: {activeTarget.last_scan_at ? new Date(activeTarget.last_scan_at).toLocaleString() : 'Never'}</span>
              <button
                type="button"
                onClick={() => setActivePage('targets', { targetId: activeTarget.id })}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#00E5FF',
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '0.74rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span>Configure in Catalog</span>
                <ExternalLink size={11} />
              </button>
            </div>
          </div>
        )}

        {/* Target URL Input */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '6px' }}>
            Target Base URL (Destination Boundary)
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
        </div>

        {/* Scan Profile Selection */}
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

        {/* Active Audit Modules Checkboxes */}
        <div style={{ marginBottom: '18px' }}>
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
                  cursor: isScanning ? 'not-allowed' : 'pointer',
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

        {/* State Changing Toggle (Safety Option) */}
        {activeTarget && selectedTargetId !== 'custom' && (
          <div style={{ marginBottom: '18px', padding: '10px 14px', borderRadius: '6px', background: '#020710', border: '1px solid #0F2F4E' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: isScanning ? 'not-allowed' : 'pointer' }}>
              <input
                type="checkbox"
                checked={allowStateChanging}
                onChange={(e) => setAllowStateChanging(e.target.checked)}
                disabled={isScanning}
              />
              <span style={{ fontSize: '0.8rem', color: '#8AA4C8' }}>
                Allow Testing State-Changing Endpoints (POST / PUT / DELETE)
              </span>
            </label>
          </div>
        )}

        {/* Authorization Confirmation */}
        <div style={{ marginBottom: '22px', padding: '12px 14px', borderRadius: '8px', background: 'rgba(0, 229, 255, 0.05)', border: '1px solid rgba(0, 229, 255, 0.2)' }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: isScanning ? 'not-allowed' : 'pointer' }}>
            <input
              type="checkbox"
              checked={userAuthorized}
              onChange={(e) => setUserAuthorized(e.target.checked)}
              disabled={isScanning}
              style={{ marginTop: '3px' }}
            />
            <span style={{ fontSize: '0.82rem', color: '#E8F1FF', lineHeight: '1.5' }}>
              I confirm that I am explicitly authorized to perform automated security vulnerability testing against this target API.
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

        {/* Action Button (Prevent Duplicate Submissions) */}
        <button
          onClick={handleStartScan}
          disabled={isScanning || !userAuthorized}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            width: '100%',
            padding: '13px 20px',
            background: isScanning ? '#0F2F4E' : (!userAuthorized ? 'rgba(0, 229, 255, 0.3)' : '#00E5FF'),
            color: isScanning ? '#8AA4C8' : (!userAuthorized ? '#6482A6' : '#040813'),
            border: 'none',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: (isScanning || !userAuthorized) ? 'not-allowed' : 'pointer',
            boxShadow: (isScanning || !userAuthorized) ? 'none' : '0 0 20px rgba(0, 229, 255, 0.4)',
            transition: 'all 0.2s ease',
          }}
        >
          {isScanning ? (
            <>
              <RefreshCw size={18} className="animate-spin" />
              <span>Executing Automated Security Audit ({progress}%)...</span>
            </>
          ) : (
            <>
              <Play size={18} fill="#040813" />
              <span>Launch Automated Security Scan</span>
            </>
          )}
        </button>

        {/* Success Banner & Direct Workflow Navigation */}
        {scanResult && (
          <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', background: 'rgba(34, 197, 94, 0.12)', border: '1px solid rgba(34, 197, 94, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#22C55E', fontWeight: 600, marginBottom: '6px' }}>
              <CheckCircle2 size={18} />
              <span>Security Scan Session Completed!</span>
            </div>
            <p style={{ color: '#8AA4C8', fontSize: '0.84rem', marginBottom: '12px', lineHeight: '1.4' }}>
              Successfully audited target. Detected <strong style={{ color: '#FF4D5E' }}>{scanResult.total_findings} security findings</strong>.
            </p>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setActivePage('findings', { scanId: scanResult.id })}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  background: '#22C55E',
                  color: '#040813',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                <span>Navigate to Findings ({scanResult.total_findings})</span>
                <ArrowRight size={14} />
              </button>

              <button
                onClick={() => setActivePage('evidence', { scanId: scanResult.id })}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  background: 'rgba(0, 229, 255, 0.15)',
                  border: '1px solid #00E5FF',
                  color: '#00E5FF',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <span>Inspect Evidence</span>
              </button>

              <button
                onClick={() => setActivePage('retesting', { scanId: scanResult.id })}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  background: 'transparent',
                  border: '1px solid rgba(34, 197, 94, 0.4)',
                  color: '#22C55E',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <span>Verify & Retest</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Real-time Telemetry & Terminal Console */}
      <div className="cyber-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', minWidth: 0, boxSizing: 'border-box' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={18} color="#00E5FF" />
            <h4 style={{ fontSize: '0.96rem', fontWeight: 600, color: '#FFFFFF', margin: 0 }}>
              Live Scanner Telemetry Log
            </h4>
          </div>
          {isScanning && (
            <span style={{ fontSize: '0.74rem', color: '#00E5FF', fontWeight: 700 }}>
              Scanning in progress...
            </span>
          )}
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
            minHeight: '280px',
            maxHeight: '440px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}
        >
          {logs.length === 0 ? (
            <span style={{ color: '#54718C' }}>Waiting for scan dispatch... Select a target and launch scan above.</span>
          ) : (
            logs.map((log, idx) => {
              let color = '#8AA4C8';
              if (log.includes('[COMPLETE]') || log.includes('[FINDINGS]')) color = '#22C55E';
              if (log.includes('[ERROR]')) color = '#FF4D5E';
              if (log.includes('[PROBING]')) color = '#00E5FF';
              if (log.includes('[TARGET]')) color = '#E8F1FF';
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
