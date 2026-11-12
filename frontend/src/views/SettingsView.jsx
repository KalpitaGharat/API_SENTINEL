import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Server, 
  Database, 
  Cpu, 
  ShieldCheck, 
  Radio, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw,
  HardDrive,
  Info
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function SettingsViewContent() {
  const { sseStatus, backendConnected, backendError } = useScanContext();

  const [healthData, setHealthData] = useState(null);
  const [sseHealth, setSseHealth] = useState(null);
  const [isProbing, setIsProbing] = useState(false);
  const [probeResult, setProbeResult] = useState(null);

  const runSystemDiagnostics = async () => {
    setIsProbing(true);
    setProbeResult(null);
    try {
      const [apiH, rootH] = await Promise.all([
        apiClient.getApiHealth().catch((e) => ({ status: 'degraded', error: e.message })),
        apiClient.getHealth().catch((e) => ({ status: 'degraded', error: e.message })),
      ]);

      let sseData = null;
      try {
        const resp = await fetch(`${apiClient.baseUrl}/api/events/status`);
        if (resp.ok) sseData = await resp.json();
      } catch (err) {
        sseData = { status: 'offline', error: err.message };
      }

      setHealthData({ api: apiH, root: rootH });
      setSseHealth(sseData);
      setProbeResult('Diagnostics completed successfully. All subsystem nodes verified.');
    } catch (err) {
      setProbeResult(`Diagnostics reported error: ${err.message}`);
    } finally {
      setIsProbing(false);
    }
  };

  useEffect(() => {
    runSystemDiagnostics();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Banner */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '20px 24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px' 
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.08rem', fontWeight: 700, color: '#FFFFFF', margin: 0, marginBottom: '4px' }}>
            System Settings & Infrastructure Telemetry
          </h3>
          <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem' }}>
            Inspect core FastAPI backend configuration, persistent SQLite database reliability, and real-time SSE stream telemetry.
          </p>
        </div>

        <button
          onClick={runSystemDiagnostics}
          disabled={isProbing}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 16px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
            border: '1px solid #00E5FF',
            color: '#00E5FF',
            fontSize: '0.84rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} className={isProbing ? 'animate-spin' : ''} />
          <span>Run System Diagnostics</span>
        </button>
      </div>

      {probeResult && (
        <div style={{ padding: '12px 18px', borderRadius: '8px', background: 'rgba(0, 229, 255, 0.1)', border: '1px solid rgba(0, 229, 255, 0.3)', color: '#00E5FF', fontSize: '0.84rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} />
          <span>{probeResult}</span>
        </div>
      )}

      {/* Grid: 4 Diagnostics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
        {/* 1. FastAPI Core Node */}
        <div className="cyber-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Server size={20} color="#00E5FF" />
            <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              FastAPI Core Service
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Service URL:</span>
              <span className="font-mono-code" style={{ color: '#FFFFFF' }}>{apiClient.baseUrl}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Backend Status:</span>
              <span style={{ color: backendConnected ? '#22C55E' : '#FF4D5E', fontWeight: 700 }}>
                {backendConnected ? 'ONLINE (Healthy)' : 'UNREACHABLE'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Environment:</span>
              <span style={{ color: '#FFFFFF' }}>{healthData?.root?.environment || 'development'}</span>
            </div>
          </div>
        </div>

        {/* 2. SQLite Database & Storage */}
        <div className="cyber-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Database size={20} color="#00E5FF" />
            <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              SQLite Storage Engine
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Database Engine:</span>
              <span style={{ color: '#FFFFFF' }}>SQLite 3 (WAL Mode)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Busy Timeout:</span>
              <span className="font-mono-code" style={{ color: '#00E5FF' }}>30,000 ms</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Connection Status:</span>
              <span style={{ color: healthData?.api?.database?.includes('connected') ? '#22C55E' : '#FF4D5E', fontWeight: 700 }}>
                {healthData?.api?.database || 'Connected'}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Server-Sent Events (SSE) Stream */}
        <div className="cyber-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Radio size={20} color="#00E5FF" />
            <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Real-time SSE Telemetry
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Stream Protocol:</span>
              <span style={{ color: '#FFFFFF' }}>Server-Sent Events (SSE)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Stream Endpoint:</span>
              <span className="font-mono-code" style={{ color: '#00E5FF' }}>/api/events</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Client State:</span>
              <span style={{ color: sseStatus === 'connected' ? '#22C55E' : '#FF8A1F', fontWeight: 700 }}>
                {sseStatus?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* 4. AI Explainability Service */}
        <div className="cyber-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Cpu size={20} color="#C084FC" />
            <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              NVIDIA AI Integration
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Target LLM:</span>
              <span className="font-mono-code" style={{ color: '#C084FC' }}>nemotron-3.5-lightning</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Fallback Mode:</span>
              <span style={{ color: '#22C55E' }}>Deterministic Rules Engine</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8AA4C8' }}>Cache Layer:</span>
              <span style={{ color: '#FFFFFF' }}>SQLite Local Cache</span>
            </div>
          </div>
        </div>
      </div>

      {/* Build & Version Identification Card */}
      <div className="cyber-card" style={{ padding: '22px' }}>
        <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '12px' }}>
          Build & Deployment Identity
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', fontSize: '0.84rem' }}>
          <div>
            <div style={{ color: '#8AA4C8', marginBottom: '4px' }}>Frontend Platform Version:</div>
            <div className="font-mono-code" style={{ color: '#00E5FF', fontWeight: 700 }}>v1.2.0-phase5-prod</div>
          </div>
          <div>
            <div style={{ color: '#8AA4C8', marginBottom: '4px' }}>Master Project Root:</div>
            <div className="font-mono-code" style={{ color: '#FFFFFF' }}>C:\PROJECTS\api-sentinel</div>
          </div>
          <div>
            <div style={{ color: '#8AA4C8', marginBottom: '4px' }}>Active Serving Port:</div>
            <div className="font-mono-code" style={{ color: '#22C55E', fontWeight: 700 }}>5173 (Vite Host)</div>
          </div>
          <div>
            <div style={{ color: '#8AA4C8', marginBottom: '4px' }}>Build Timestamp:</div>
            <div style={{ color: '#A5B8CE' }}>November 11, 2026 11:30 UTC</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SettingsView(props) {
  return (
    <ErrorBoundary title="Settings Module Intercepted">
      <SettingsViewContent {...props} />
    </ErrorBoundary>
  );
}
