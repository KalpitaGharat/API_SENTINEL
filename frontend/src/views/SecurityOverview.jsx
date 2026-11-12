import React, { useState } from 'react';
import KpiCards from '../components/KpiCards';
import SeverityDonutChart from '../components/SeverityDonutChart';
import ScanActivityChart from '../components/ScanActivityChart';
import RecentFindingsTable from '../components/RecentFindingsTable';
import LastScanSummary from '../components/LastScanSummary';
import { CheckCircle2, ShieldCheck, AlertTriangle, Sparkles, ArrowRight, Cpu, Layers } from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import ErrorBoundary from '../components/ErrorBoundary';

function SecurityOverviewContent({ setActivePage }) {
  const { backendConnected, backendError } = useScanContext();
  const [showTriggerScanline, setShowTriggerScanline] = useState(false);

  const handleTriggerScan = () => {
    setActivePage('new_scan');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative' }}>
      {/* Backend Disconnected Warning */}
      {!backendConnected && (
        <div 
          style={{
            padding: '14px 18px',
            borderRadius: '10px',
            background: 'rgba(255, 77, 94, 0.15)',
            border: '1px solid rgba(255, 77, 94, 0.4)',
            color: '#FF4D5E',
            fontSize: '0.86rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <AlertTriangle size={20} />
          <div>
            <strong>Backend Unreachable:</strong> {backendError || 'Unable to connect to FastAPI backend at http://127.0.0.1:8000. Please start the backend service.'}
          </div>
        </div>
      )}

      {/* Row 1: 4 Equal-width KPI Cards */}
      <KpiCards />

      {/* Row 1.5: NVIDIA Nemotron AI Spotlight Banner */}
      <div
        className="cyber-card"
        style={{
          padding: '18px 24px',
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(6, 18, 38, 0.9) 100%)',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          borderRadius: '12px',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.35), 0 0 16px rgba(139, 92, 246, 0.15)',
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
            height: '2px',
            background: 'linear-gradient(90deg, #8B5CF6 0%, #00E5FF 50%, #8B5CF6 100%)',
          }}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, minWidth: '300px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '10px',
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1.5px solid rgba(139, 92, 246, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(139, 92, 246, 0.4)',
              flexShrink: 0,
            }}
          >
            <Sparkles size={22} color="#C084FC" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                NVIDIA Nemotron AI Security Intelligence
              </h3>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  background: 'rgba(139, 92, 246, 0.25)',
                  border: '1px solid rgba(139, 92, 246, 0.5)',
                  color: '#C084FC',
                }}
              >
                ACTIVE & INTEGRATED
              </span>
            </div>
            <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem', lineHeight: '1.4' }}>
              Explainable AI models generate plain-English vulnerability breakdowns, realistic threat & regulatory impact analysis, and copy-paste remediation code.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem', color: '#6482A6' }}>
            <span style={{ padding: '4px 8px', background: 'rgba(2, 7, 16, 0.6)', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
              ⚡ Live Nemotron
            </span>
            <span style={{ padding: '4px 8px', background: 'rgba(2, 7, 16, 0.6)', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
              🛡️ Offline Fallback
            </span>
            <span style={{ padding: '4px 8px', background: 'rgba(2, 7, 16, 0.6)', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
              💾 SQLite Cached
            </span>
          </div>

          <button
            onClick={() => setActivePage('findings')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
              border: '1px solid #A78BFA',
              color: '#FFFFFF',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 0 16px rgba(139, 92, 246, 0.4)',
              transition: 'all 0.2s ease',
            }}
          >
            <span>Explore AI Findings</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {/* Row 2: Severity Distribution + Scan Activity */}
      <div 
        className="charts-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: '32% calc(68% - 18px)',
          gap: '18px',
          position: 'relative'
        }}
      >
        <SeverityDonutChart />
        <ScanActivityChart onTriggerScan={handleTriggerScan} />
      </div>

      {/* Row 3: Recent Vulnerability Findings Table + Last Scan Summary */}
      <div 
        className="bottom-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'calc(68% - 18px) 32%',
          gap: '18px',
          position: 'relative'
        }}
      >
        <RecentFindingsTable 
          onViewAll={() => setActivePage('findings')} 
          onInspectFinding={() => setActivePage('evidence')}
        />
        <LastScanSummary onTriggerScan={handleTriggerScan} />
      </div>
    </div>
  );
}

export default function SecurityOverview(props) {
  return (
    <ErrorBoundary title="Security Overview Intercepted">
      <SecurityOverviewContent {...props} />
    </ErrorBoundary>
  );
}
