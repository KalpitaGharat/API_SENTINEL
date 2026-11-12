import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Search, 
  ArrowRight, 
  Play, 
  Sparkles, 
  CheckCircle2, 
  Terminal, 
  RefreshCw 
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import AttackEvidenceInspector from '../components/AttackEvidenceInspector';
import ErrorBoundary from '../components/ErrorBoundary';

function AttackEvidenceWorkspaceContent({ setActivePage, initialFindingId }) {
  const { 
    scans, 
    selectedScanId, 
    selectScan, 
    findings, 
    activeScan, 
    selectedFindingId: ctxFindingId,
    selectFinding,
    isLoadingFindings 
  } = useScanContext();

  const [selectedFindingId, setSelectedFindingId] = useState(initialFindingId || ctxFindingId || '');

  // Synchronize initialFindingId if provided via deep link
  useEffect(() => {
    if (initialFindingId) {
      setSelectedFindingId(initialFindingId);
    }
  }, [initialFindingId]);

  // Synchronize when findings load or change
  useEffect(() => {
    if (findings && findings.length > 0) {
      if (!selectedFindingId || !findings.some((f) => f.id === selectedFindingId)) {
        // Prefer critical or BOLA finding first
        const priorityFinding = findings.find(
          (f) => (f.category || '').toUpperCase().includes('BOLA') || (f.severity || '').toLowerCase() === 'critical'
        );
        const autoId = priorityFinding ? priorityFinding.id : findings[0].id;
        setSelectedFindingId(autoId);
        if (selectFinding) selectFinding(autoId);
      }
    } else {
      setSelectedFindingId('');
    }
  }, [findings, selectedFindingId, selectFinding]);

  const handleSelectFinding = (findingId) => {
    setSelectedFindingId(findingId);
    if (selectFinding) selectFinding(findingId);
    try {
      window.location.hash = `evidence?finding_id=${findingId}`;
    } catch (_) {}
  };

  const currentFinding = (findings || []).find((f) => f.id === selectedFindingId) || (findings && findings[0]) || null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Finding Selector & Telemetry Bar */}
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
            <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>Finding to Inspect:</span>
            <select
              value={selectedFindingId}
              onChange={(e) => handleSelectFinding(e.target.value)}
              disabled={!findings || findings.length === 0}
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
              {(!findings || findings.length === 0) && (
                <option value="">No Findings Detected</option>
              )}
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
            onClick={() => setActivePage('findings')}
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
            <span>Back to Findings Table</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Display */}
      {!currentFinding ? (
        <div 
          className="cyber-card" 
          style={{ 
            padding: '48px 24px', 
            textAlign: 'center', 
            color: '#8AA4C8',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '14px'
          }}
        >
          <div 
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '14px',
              background: 'rgba(0, 229, 255, 0.1)',
              border: '1px solid rgba(0, 229, 255, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={28} color="#00E5FF" />
          </div>
          <h3 style={{ fontSize: '1.15rem', color: '#FFFFFF', margin: 0, fontWeight: 700 }}>
            No Vulnerability Finding Selected
          </h3>
          <p style={{ maxWidth: '480px', fontSize: '0.86rem', lineHeight: '1.5', margin: 0 }}>
            Run an automated security scan against an authorized API target to capture technical HTTP telemetry, request/response evidence, and SHA-256 cryptographic proof.
          </p>
          <button
            onClick={() => setActivePage('scans')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '6px',
              padding: '9px 18px',
              borderRadius: '8px',
              background: '#00E5FF',
              color: '#040813',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.86rem',
              cursor: 'pointer',
            }}
          >
            <Play size={15} />
            <span>Launch Security Scan</span>
          </button>
        </div>
      ) : (
        /* Full-Screen Dedicated Workspace Mode */
        <div style={{ position: 'relative', width: '100%' }}>
          <AttackEvidenceInspector
            finding={currentFinding}
            scan={activeScan}
            embedded={true}
            onClose={() => setActivePage('findings')}
            onNavigateToRetest={(f) => setActivePage('retesting', { findingId: f?.id || currentFinding.id })}
            onNavigateToAi={(f) => setActivePage('ai_analysis', { findingId: f?.id || currentFinding.id })}
            onNavigateToAudit={(f) => setActivePage('audit_history', { findingId: f?.id || currentFinding.id })}
          />
        </div>
      )}
    </div>
  );
}

export default function AttackEvidenceWorkspace(props) {
  return (
    <ErrorBoundary title="Attack Evidence Workspace Intercepted">
      <AttackEvidenceWorkspaceContent {...props} />
    </ErrorBoundary>
  );
}
