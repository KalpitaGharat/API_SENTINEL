import React, { useState } from 'react';
import { 
  Sparkles, 
  Cpu, 
  ShieldAlert, 
  ShieldCheck, 
  Search, 
  RefreshCw, 
  Terminal, 
  Layers, 
  Lock, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import AiExplanationPanel from '../components/AiExplanationPanel';
import ErrorBoundary from '../components/ErrorBoundary';

function AiSecurityAnalysisContent({ setActivePage }) {
  const { scans, selectedScanId, selectScan, findings, isLoadingFindings, refreshFindings } = useScanContext();
  const [selectedFindingId, setSelectedFindingId] = useState(null);

  // Auto-select first finding if none selected
  const activeFinding = (findings || []).find((f) => f.id === selectedFindingId) || (findings || [])[0] || null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top AI Engine Status Banner */}
      <div
        className="cyber-card"
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(6, 18, 38, 0.95) 100%)',
          border: '1px solid rgba(139, 92, 246, 0.45)',
          borderRadius: '12px',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(139, 92, 246, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, #8B5CF6 0%, #00E5FF 50%, #8B5CF6 100%)',
          }}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, minWidth: '320px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'rgba(139, 92, 246, 0.25)',
              border: '1.5px solid rgba(139, 92, 246, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(139, 92, 246, 0.5)',
              flexShrink: 0,
            }}
          >
            <Sparkles size={24} color="#C084FC" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF', margin: 0 }}>
                NVIDIA Nemotron AI Security Intelligence Hub
              </h3>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  background: 'rgba(139, 92, 246, 0.3)',
                  border: '1px solid rgba(139, 92, 246, 0.6)',
                  color: '#C084FC',
                }}
              >
                ONLINE & ACTIVE
              </span>
            </div>
            <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem', lineHeight: '1.4' }}>
              Select any detected vulnerability to generate explainable plain-English breakdowns, simulated attack vectors, and verified code fixes.
            </p>
          </div>
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
              color: '#00E5FF',
              fontSize: '0.84rem',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '240px',
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
      </div>

      {/* Main 2-Column Layout: Finding Selector List on Left, Deep AI Panel on Right */}
      {isLoadingFindings ? (
        <div className="cyber-card" style={{ padding: '60px 20px', textAlign: 'center', color: '#8AA4C8' }}>
          <RefreshCw size={36} color="#8B5CF6" className="spin" style={{ margin: '0 auto 16px auto' }} />
          <h4 style={{ color: '#FFFFFF', fontSize: '1.05rem', marginBottom: '8px' }}>
            Retrieving Security Findings & Telemetry...
          </h4>
          <p style={{ fontSize: '0.84rem', color: '#6482A6' }}>
            Fetching vulnerability records and cached AI explanations from SQLite.
          </p>
        </div>
      ) : findings.length === 0 ? (
        <div className="cyber-card" style={{ padding: '60px 20px', textAlign: 'center', color: '#8AA4C8' }}>
          <ShieldCheck size={40} color="#00E5FF" style={{ margin: '0 auto 16px auto' }} />
          <h4 style={{ color: '#FFFFFF', fontSize: '1.1rem', marginBottom: '8px' }}>
            No Vulnerabilities Available for AI Analysis
          </h4>
          <p style={{ fontSize: '0.86rem', color: '#6482A6', maxWidth: '440px', margin: '0 auto 20px auto' }}>
            Launch a security scan from the New Security Scan tab to detect vulnerabilities and unlock deep AI explainability.
          </p>
          <button
            onClick={() => setActivePage('new_scan')}
            style={{
              padding: '10px 20px',
              background: '#00E5FF',
              color: '#040813',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '0.86rem',
              cursor: 'pointer',
            }}
          >
            Launch Security Scan
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '22px' }}>
          {/* Left Column: Finding Selector List */}
          <div className="cyber-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px', height: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid #0F2F4E' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#FFFFFF' }}>
                Detected Findings ({findings.length})
              </span>
              <span style={{ fontSize: '0.76rem', color: '#8AA4C8' }}>Click to Analyze</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '600px', overflowY: 'auto' }}>
              {findings.map((f) => {
                const isSelected = activeFinding?.id === f.id;
                const isCrit = f.severity?.toLowerCase() === 'critical';
                const isHigh = f.severity?.toLowerCase() === 'high';
                const sevColor = isCrit ? '#FF4D5E' : isHigh ? '#FF8A1F' : '#00E5FF';

                return (
                  <div
                    key={f.id}
                    onClick={() => setSelectedFindingId(f.id)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(139, 92, 246, 0.2)' : 'rgba(4, 12, 24, 0.6)',
                      border: isSelected ? '1.5px solid #8B5CF6' : '1px solid #0F2F4E',
                      borderLeft: `4px solid ${sevColor}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: sevColor,
                        }}
                      >
                        {f.severity?.toUpperCase()}
                      </span>
                      {f.ai_explanation && (
                        <span style={{ fontSize: '0.72rem', color: '#C084FC', display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <Sparkles size={11} />
                          <span>Analyzed</span>
                        </span>
                      )}
                    </div>

                    <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '4px' }}>
                      {f.vulnerability}
                    </div>

                    <div className="font-mono-code" style={{ fontSize: '0.78rem', color: '#8AA4C8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {f.endpoint}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Active Finding Detail & Complete AI Explanation Panel */}
          {activeFinding && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Finding Overview Summary Box */}
              <div className="cyber-card" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span
                        style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          background: `${activeFinding.severity === 'Critical' ? '#FF4D5E' : '#FF8A1F'}22`,
                          color: activeFinding.severity === 'Critical' ? '#FF4D5E' : '#FF8A1F',
                          border: `1px solid ${activeFinding.severity === 'Critical' ? '#FF4D5E' : '#FF8A1F'}55`,
                        }}
                      >
                        {activeFinding.severity?.toUpperCase()}
                      </span>
                      <span className="font-mono-code" style={{ color: '#00E5FF', fontSize: '0.84rem' }}>
                        {activeFinding.endpoint}
                      </span>
                    </div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                      {activeFinding.vulnerability}
                    </h3>
                  </div>

                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      background: activeFinding.status === 'Resolved' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)',
                      color: activeFinding.status === 'Resolved' ? '#22C55E' : '#FF4D5E',
                      border: `1px solid ${activeFinding.status === 'Resolved' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255, 77, 94, 0.4)'}`,
                    }}
                  >
                    {activeFinding.status?.toUpperCase() || 'OPEN'}
                  </span>
                </div>

                <p style={{ color: '#A5B8CE', fontSize: '0.88rem', lineHeight: '1.6', marginBottom: '16px' }}>
                  {activeFinding.description}
                </p>

                {/* HTTP Evidence Telemetry */}
                {activeFinding.evidence && (
                  <div style={{ background: '#020710', border: '1px solid #0F2F4E', borderRadius: '8px', padding: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                      <Terminal size={14} color="#00E5FF" />
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#00E5FF' }}>
                        Technical Evidence & Observed Telemetry
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', fontSize: '0.8rem' }}>
                      <div>
                        <span style={{ color: '#6482A6' }}>Test Principal:</span>{' '}
                        <strong style={{ color: '#FFFFFF' }}>{activeFinding.evidence.test_user || 'Unauthenticated'}</strong>
                      </div>
                      <div>
                        <span style={{ color: '#6482A6' }}>Observed Status:</span>{' '}
                        <strong style={{ color: '#FF4D5E' }}>HTTP {activeFinding.evidence.observed_status}</strong>
                      </div>
                      <div>
                        <span style={{ color: '#6482A6' }}>Expected Status:</span>{' '}
                        <strong style={{ color: '#22C55E' }}>HTTP {activeFinding.evidence.expected_status || 403}</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* NVIDIA Nemotron AI Analysis Container */}
              <AiExplanationPanel
                finding={activeFinding}
                onExplanationUpdated={() => refreshFindings(selectedScanId)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AiSecurityAnalysis(props) {
  return (
    <ErrorBoundary title="AI Security Analysis Intercepted">
      <AiSecurityAnalysisContent {...props} />
    </ErrorBoundary>
  );
}
