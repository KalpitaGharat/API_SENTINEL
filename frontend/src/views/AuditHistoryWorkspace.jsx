import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Clock, 
  History, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle,
  ShieldCheck, 
  ShieldAlert, 
  RefreshCw, 
  ExternalLink,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  Terminal,
  Copy,
  Check
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function AuditHistoryWorkspaceContent({ setActivePage, initialFindingId }) {
  const { 
    scans, 
    selectedScanId, 
    selectScan, 
    findings, 
    selectedFindingId: ctxFindingId,
    selectFinding 
  } = useScanContext();

  const [scopeFindingId, setScopeFindingId] = useState(initialFindingId || ctxFindingId || 'all');
  const [historyRecords, setHistoryRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRecordId, setExpandedRecordId] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Sync initialFindingId if provided via URL deep link
  useEffect(() => {
    if (initialFindingId) {
      setScopeFindingId(initialFindingId);
    }
  }, [initialFindingId]);

  // Load ledger: either for a single finding or aggregate across all findings in the active scan
  const loadHistory = useCallback(async (scopeId, currentFindings) => {
    setIsLoading(true);
    setError(null);
    try {
      if (scopeId && scopeId !== 'all') {
        const data = await apiClient.getFindingHistory(scopeId);
        const list = (data?.history || []).map((rec) => {
          const parentFinding = (currentFindings || []).find((f) => f.id === rec.finding_id);
          return {
            ...rec,
            endpoint: parentFinding?.endpoint || 'N/A',
            vulnerability: parentFinding?.vulnerability || 'Security Finding',
            severity: parentFinding?.severity || 'Medium',
          };
        });
        list.sort((a, b) => new Date(b.retested_at) - new Date(a.retested_at));
        setHistoryRecords(list);
      } else {
        // Aggregate ledger: load history for all findings in current scan session
        if (!currentFindings || currentFindings.length === 0) {
          setHistoryRecords([]);
          setIsLoading(false);
          return;
        }

        const historyPromises = currentFindings.map((f) =>
          apiClient.getFindingHistory(f.id)
            .then((data) => (data?.history || []).map((rec) => ({
              ...rec,
              endpoint: f.endpoint,
              vulnerability: f.vulnerability,
              severity: f.severity,
            })))
            .catch(() => [])
        );

        const results = await Promise.all(historyPromises);
        const flattened = results.flat();
        flattened.sort((a, b) => new Date(b.retested_at) - new Date(a.retested_at));
        setHistoryRecords(flattened);
      }
    } catch (err) {
      console.warn('[AuditHistory] Failed to load history:', err);
      setError('Unable to fetch audit records from SQLite persistence.');
      setHistoryRecords([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory(scopeFindingId, findings);
  }, [scopeFindingId, findings, loadHistory]);

  const handleScopeChange = (newScopeId) => {
    setScopeFindingId(newScopeId);
    if (newScopeId && newScopeId !== 'all') {
      if (selectFinding) selectFinding(newScopeId);
      try {
        window.location.hash = `audit?finding_id=${newScopeId}`;
      } catch (_) {}
    } else {
      try {
        window.location.hash = 'audit';
      } catch (_) {}
    }
  };

  const copyToClipboard = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const activeFinding = (findings || []).find((f) => f.id === scopeFindingId) || null;

  // Filter records by status and search query
  const filteredRecords = useMemo(() => {
    return historyRecords.filter((rec) => {
      // Status filter
      if (statusFilter !== 'All') {
        const isResolved = rec.new_status === 'Resolved' || Boolean(rec.verified);
        const isStillVuln = rec.new_status === 'Still Vulnerable' || (rec.verified === false && rec.new_status !== 'Needs Review');
        const isNeedsReview = (rec.new_status || '').toLowerCase().includes('review');

        if (statusFilter === 'Resolved' && !isResolved) return false;
        if (statusFilter === 'Still Vulnerable' && !isStillVuln) return false;
        if (statusFilter === 'Needs Review' && !isNeedsReview) return false;
      }

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesId = (rec.id || '').toLowerCase().includes(q);
        const matchesVuln = (rec.vulnerability || '').toLowerCase().includes(q);
        const matchesEndpoint = (rec.endpoint || '').toLowerCase().includes(q);
        const matchesStatus = (rec.new_status || '').toLowerCase().includes(q);
        if (!matchesId && !matchesVuln && !matchesEndpoint && !matchesStatus) {
          return false;
        }
      }

      return true;
    });
  }, [historyRecords, statusFilter, searchQuery]);

  const getVerdictBadge = (rec) => {
    const statusLower = (rec.new_status || '').toLowerCase();
    const isVerified = Boolean(rec.verified) || statusLower === 'resolved';
    const isNeedsReview = statusLower.includes('review');

    if (isNeedsReview) {
      return {
        bg: 'rgba(255, 138, 31, 0.15)',
        text: '#FF8A1F',
        border: 'rgba(255, 138, 31, 0.4)',
        label: 'NEEDS REVIEW',
        icon: Clock,
      };
    }

    if (isVerified) {
      return {
        bg: 'rgba(34, 197, 94, 0.15)',
        text: '#22C55E',
        border: 'rgba(34, 197, 94, 0.4)',
        label: 'VERIFIED RESOLVED',
        icon: CheckCircle2,
      };
    }

    return {
      bg: 'rgba(255, 77, 94, 0.15)',
      text: '#FF4D5E',
      border: 'rgba(255, 77, 94, 0.4)',
      label: 'STILL VULNERABLE',
      icon: AlertTriangle,
    };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Scope & Controls Bar */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '16px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          flexWrap: 'wrap', 
          gap: '14px' 
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>Active Scan:</span>
            <select
              value={selectedScanId || ''}
              onChange={(e) => selectScan(e.target.value)}
              style={{
                padding: '7px 12px',
                background: '#04101F',
                border: '1px solid #0F2F4E',
                borderRadius: '8px',
                color: '#00E5FF',
                fontSize: '0.84rem',
                outline: 'none',
                cursor: 'pointer',
                maxWidth: '220px',
              }}
            >
              {scans.length === 0 && <option value="">No Scans Recorded</option>}
              {scans.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.target_url} ({s.id.substring(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>Audit Scope:</span>
            <select
              value={scopeFindingId}
              onChange={(e) => handleScopeChange(e.target.value)}
              style={{
                padding: '7px 12px',
                background: '#04101F',
                border: '1px solid #0F2F4E',
                borderRadius: '8px',
                color: '#FFFFFF',
                fontSize: '0.84rem',
                outline: 'none',
                cursor: 'pointer',
                maxWidth: '340px',
              }}
            >
              <option value="all">All Findings in Scan (Aggregate Session Ledger)</option>
              {(findings || []).map((f) => (
                <option key={f.id} value={f.id}>
                  [{f.severity?.toUpperCase()}] {f.vulnerability} - {f.endpoint}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => loadHistory(scopeFindingId, findings)}
            disabled={isLoading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: '#07182B',
              border: '1px solid #0F2F4E',
              color: '#8AA4C8',
              borderRadius: '8px',
              padding: '7px 14px',
              fontSize: '0.82rem',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>Refresh Ledger</span>
          </button>
        </div>
      </div>

      {/* Filter and Telemetry Header Card */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '14px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '240px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '380px' }}>
            <Search size={15} color="#8AA4C8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search audit records by endpoint, title, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 32px',
                background: '#04101F',
                border: '1px solid #0F2F4E',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '0.82rem',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={14} color="#8AA4C8" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '7px 12px',
                background: '#04101F',
                border: '1px solid #0F2F4E',
                borderRadius: '6px',
                color: '#8AA4C8',
                fontSize: '0.82rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="All">All Verification Statuses</option>
              <option value="Resolved">Verified Resolved</option>
              <option value="Still Vulnerable">Still Vulnerable</option>
              <option value="Needs Review">Needs Review</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: '#8AA4C8' }}>
          <span>Total Audit Records:</span>
          <strong style={{ color: '#00E5FF', fontFamily: 'monospace', fontSize: '0.9rem' }}>
            {filteredRecords.length}
          </strong>
        </div>
      </div>

      {/* Main Ledger Table */}
      <div className="cyber-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={20} color="#00E5FF" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Immutable Verification Audit Trail
            </h3>
          </div>

          {activeFinding ? (
            <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>
              Scoped Target: <strong style={{ color: '#E8F1FF' }}>{activeFinding.endpoint}</strong> ({activeFinding.vulnerability})
            </span>
          ) : (
            <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>
              Scope: <strong style={{ color: '#00E5FF' }}>Aggregate Scan Session Ledger</strong>
            </span>
          )}
        </div>

        {isLoading ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#8AA4C8' }}>
            <RefreshCw size={24} className="animate-spin" color="#00E5FF" style={{ margin: '0 auto 10px auto' }} />
            <div>Loading verified audit records from SQLite persistence...</div>
          </div>
        ) : error ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#FF4D5E' }}>
            <AlertCircle size={28} color="#FF4D5E" style={{ margin: '0 auto 10px auto' }} />
            <div>{error}</div>
            <button 
              onClick={() => loadHistory(scopeFindingId, findings)}
              style={{
                marginTop: '12px',
                padding: '6px 14px',
                background: 'rgba(0, 229, 255, 0.1)',
                border: '1px solid #00E5FF',
                borderRadius: '6px',
                color: '#00E5FF',
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              Retry
            </button>
          </div>
        ) : filteredRecords.length === 0 ? (
          <div style={{ padding: '48px 20px', textAlign: 'center', color: '#8AA4C8' }}>
            <div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(0, 229, 255, 0.1)',
                border: '1px solid rgba(0, 229, 255, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 14px auto',
              }}
            >
              <Clock size={24} color="#00E5FF" />
            </div>
            <h4 style={{ fontSize: '1rem', color: '#FFFFFF', margin: '0 0 6px 0', fontWeight: 600 }}>
              No Verification Probes Recorded in this Audit Scope
            </h4>
            <p style={{ maxWidth: '440px', margin: '0 auto 16px auto', fontSize: '0.84rem', lineHeight: '1.5' }}>
              Once you apply a remediation patch, trigger a targeted regression probe in the Verification & Retesting workbench to confirm the fix and permanently append audit records to this ledger.
            </p>
            <button
              onClick={() => setActivePage('retesting', { findingId: scopeFindingId !== 'all' ? scopeFindingId : null })}
              style={{
                padding: '8px 18px',
                background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(34, 197, 94, 0.2) 100%)',
                color: '#00E5FF',
                border: '1px solid #00E5FF',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.84rem',
                cursor: 'pointer',
              }}
            >
              Launch Verification in Retesting Workbench
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0F2F4E', color: '#8AA4C8', textAlign: 'left' }}>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Audit ID</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Timestamp</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Target Endpoint & Vulnerability</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>State Transition</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600 }}>Observed Telemetry</th>
                  <th style={{ padding: '10px 12px', fontWeight: 600, textAlign: 'right' }}>Remediation Verdict</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((r, idx) => {
                  const verdict = getVerdictBadge(r);
                  const VerdictIcon = verdict.icon;
                  const isExpanded = expandedRecordId === (r.id || idx);
                  const observedStatus = r.observed_result?.status_code || r.observed_result?.observed_status || '403';
                  const ownerProbe = r.observed_result?.owner_probe;
                  const attackerProbe = r.observed_result?.attacker_probe;

                  return (
                    <React.Fragment key={r.id || idx}>
                      <tr 
                        onClick={() => setExpandedRecordId(isExpanded ? null : (r.id || idx))}
                        style={{
                          borderBottom: isExpanded ? 'none' : '1px solid rgba(15, 47, 78, 0.4)',
                          background: isExpanded 
                            ? 'rgba(4, 16, 31, 0.8)' 
                            : (idx % 2 === 0 ? 'transparent' : 'rgba(4, 16, 31, 0.4)'),
                          cursor: 'pointer',
                          transition: 'background 0.15s ease',
                        }}
                      >
                        <td style={{ padding: '12px', color: '#00E5FF' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span className="font-mono-code">{r.id?.substring(0, 8)}...</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(r.id, r.id);
                              }}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: copiedId === r.id ? '#22C55E' : '#6482A6',
                                cursor: 'pointer',
                                padding: '2px',
                              }}
                              title="Copy full Audit ID"
                            >
                              {copiedId === r.id ? <Check size={11} /> : <Copy size={11} />}
                            </button>
                          </div>
                        </td>
                        <td style={{ padding: '12px', color: '#8AA4C8', whiteSpace: 'nowrap' }}>
                          {r.retested_at ? new Date(r.retested_at).toLocaleString() : 'N/A'}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <div style={{ fontWeight: 600, color: '#E8F1FF' }}>{r.vulnerability}</div>
                          <div className="font-mono-code" style={{ fontSize: '0.76rem', color: '#6482A6', marginTop: '2px' }}>
                            {r.endpoint}
                          </div>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'monospace' }}>
                            <span style={{ color: '#FF8A1F' }}>{r.previous_status || 'Open'}</span>
                            <ArrowRight size={12} color="#8AA4C8" />
                            <span style={{ color: verdict.text, fontWeight: 700 }}>{r.new_status || 'Resolved'}</span>
                          </div>
                        </td>
                        <td className="font-mono-code" style={{ padding: '12px', color: '#FFFFFF' }}>
                          HTTP {observedStatus}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              fontSize: '0.74rem',
                              fontWeight: 700,
                              background: verdict.bg,
                              color: verdict.text,
                              border: `1px solid ${verdict.border}`,
                            }}
                          >
                            <VerdictIcon size={12} />
                            <span>{verdict.label}</span>
                          </span>
                        </td>
                      </tr>

                      {/* Expandable Probe Telemetry Drawer */}
                      {isExpanded && (
                        <tr style={{ borderBottom: '1px solid rgba(15, 47, 78, 0.6)', background: 'rgba(2, 8, 18, 0.95)' }}>
                          <td colSpan={6} style={{ padding: '16px 20px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                                <div style={{ fontSize: '0.84rem', color: '#00E5FF', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <Terminal size={15} />
                                  <span>Automated Dual-Probe Verification Telemetry</span>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <button
                                    onClick={() => setActivePage('evidence', { findingId: r.finding_id })}
                                    style={{
                                      padding: '5px 12px',
                                      background: 'rgba(0, 229, 255, 0.12)',
                                      border: '1px solid rgba(0, 229, 255, 0.4)',
                                      borderRadius: '6px',
                                      color: '#00E5FF',
                                      fontSize: '0.76rem',
                                      fontWeight: 600,
                                      cursor: 'pointer',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '5px',
                                    }}
                                  >
                                    <ExternalLink size={12} />
                                    <span>Inspect Attack Evidence</span>
                                  </button>

                                  <button
                                    onClick={() => setActivePage('retesting', { findingId: r.finding_id })}
                                    style={{
                                      padding: '5px 12px',
                                      background: 'rgba(34, 197, 94, 0.15)',
                                      border: '1px solid rgba(34, 197, 94, 0.4)',
                                      borderRadius: '6px',
                                      color: '#22C55E',
                                      fontSize: '0.76rem',
                                      fontWeight: 600,
                                      cursor: 'pointer',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '5px',
                                    }}
                                  >
                                    <RefreshCw size={12} />
                                    <span>Re-Verify in Workbench</span>
                                  </button>
                                </div>
                              </div>

                              {r.observed_result?.message && (
                                <div style={{ padding: '10px 14px', background: '#040F1E', borderRadius: '6px', border: '1px solid #0F2F4E', color: '#E8F1FF', fontSize: '0.82rem', lineHeight: '1.5' }}>
                                  {r.observed_result.message}
                                </div>
                              )}

                              {/* Dual Probe Matrix */}
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
                                {/* Owner Probe */}
                                <div style={{ background: '#040F1E', padding: '12px', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
                                  <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase', marginBottom: '6px' }}>
                                    Legitimate Owner Baseline Probe
                                  </div>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem' }}>
                                    <div>Method: <strong style={{ color: '#00E5FF' }}>{ownerProbe?.method || 'GET'}</strong></div>
                                    <div className="font-mono-code" style={{ fontSize: '0.74rem', color: '#8AA4C8', wordBreak: 'break-all' }}>
                                      {ownerProbe?.url || r.endpoint}
                                    </div>
                                    <div>Status: <strong style={{ color: ownerProbe?.status_code === 200 ? '#22C55E' : '#FF8A1F' }}>HTTP {ownerProbe?.status_code || 200}</strong></div>
                                    <div>Access Granted: <strong style={{ color: '#22C55E' }}>{ownerProbe?.access_granted ? 'Yes (Expected)' : 'Verified'}</strong></div>
                                    {ownerProbe?.duration_ms && <div>Latency: <span style={{ color: '#8AA4C8' }}>{ownerProbe.duration_ms} ms</span></div>}
                                  </div>
                                </div>

                                {/* Attacker Probe */}
                                <div style={{ background: '#040F1E', padding: '12px', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
                                  <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase', marginBottom: '6px' }}>
                                    Cross-Tenant Attacker Probe
                                  </div>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem' }}>
                                    <div>Method: <strong style={{ color: '#00E5FF' }}>{attackerProbe?.method || 'GET'}</strong></div>
                                    <div className="font-mono-code" style={{ fontSize: '0.74rem', color: '#8AA4C8', wordBreak: 'break-all' }}>
                                      {attackerProbe?.url || r.endpoint}
                                    </div>
                                    <div>Status: <strong style={{ color: attackerProbe?.status_code === 403 ? '#22C55E' : '#FF4D5E' }}>HTTP {attackerProbe?.status_code || observedStatus}</strong></div>
                                    <div>Access Denied: <strong style={{ color: attackerProbe?.access_denied ? '#22C55E' : '#FF4D5E' }}>{attackerProbe?.access_denied ? 'Yes (Enforced)' : 'No'}</strong></div>
                                    <div>Foreign Data Exposed: <strong style={{ color: attackerProbe?.foreign_data_exposed ? '#FF4D5E' : '#22C55E' }}>{attackerProbe?.foreign_data_exposed ? 'LEAKED' : 'None (Protected)'}</strong></div>
                                    {attackerProbe?.duration_ms && <div>Latency: <span style={{ color: '#8AA4C8' }}>{attackerProbe.duration_ms} ms</span></div>}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuditHistoryWorkspace(props) {
  return (
    <ErrorBoundary title="Audit History Workspace Intercepted">
      <AuditHistoryWorkspaceContent {...props} />
    </ErrorBoundary>
  );
}
