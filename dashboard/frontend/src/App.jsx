import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AmbientCyberBackground from './components/AmbientCyberBackground';
import CriticalAlertModal from './components/CriticalAlertModal';
import SecurityOverview from './views/SecurityOverview';
import NewSecurityScan from './views/NewSecurityScan';
import VulnerabilityFindings from './views/VulnerabilityFindings';
import AiSecurityAnalysis from './views/AiSecurityAnalysis';
import RetestingVerification from './views/RetestingVerification';
import ScanHistory from './views/ScanHistory';
import NotificationsView from './views/NotificationsView';
import Reports from './views/Reports';
import SettingsView from './views/SettingsView';
import { ScanProvider, useScanContext } from './context/ScanContext';
import ErrorBoundary from './components/ErrorBoundary';

function AppContent() {
  const getInitialPage = () => {
    const hash = window.location.hash.replace('#', '');
    return ['overview', 'new_scan', 'history', 'findings', 'ai_analysis', 'retesting', 'notifications', 'reports', 'settings'].includes(hash)
      ? hash
      : 'overview';
  };

  const [activePage, setActivePageState] = useState(getInitialPage);
  const { activePopupAlert, acknowledgeAlert, selectScan } = useScanContext();

  const setActivePage = (page) => {
    setActivePageState(page);
    try {
      window.location.hash = page;
    } catch (_) {}
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash && hash !== activePage) {
        setActivePageState(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [activePage]);

  const pageHeaders = {
    overview: {
      title: 'Security Overview',
      subtitle: 'Real-time telemetry of your API security posture, findings, and scan activity.'
    },
    new_scan: {
      title: 'New Security Scan',
      subtitle: 'Configure target API boundaries, scan profiles, and launch automated security audits.'
    },
    history: {
      title: 'Scan History',
      subtitle: 'Complete chronological audit trail of all security scans, test runs, and regression probes.'
    },
    findings: {
      title: 'Vulnerability Findings',
      subtitle: 'Explore detected security vulnerabilities, technical HTTP evidence, and NVIDIA Nemotron AI explanations.'
    },
    ai_analysis: {
      title: 'NVIDIA Nemotron AI Security Analysis',
      subtitle: 'Deep explainable intelligence: contextual vulnerability breakdowns, simulated threat scenarios, and remediation code.'
    },
    retesting: {
      title: 'Verification & Retesting',
      subtitle: 'Automated targeted regression probes to mathematically verify security remediation on patched endpoints.'
    },
    notifications: {
      title: 'Security Notifications & Telemetry Feed',
      subtitle: 'Real-time stream of discovered vulnerabilities, scan lifecycle events, and audit logs.'
    },
    reports: {
      title: 'Security & Compliance Reports',
      subtitle: 'Export executive summaries, OWASP API Top 10 compliance scorecards, and audit logs.'
    },
    settings: {
      title: 'System Settings & Infrastructure',
      subtitle: 'FastAPI core node status, SQLite persistence health, and real-time Server-Sent Events (SSE) telemetry.'
    }
  };

  const currentHeader = pageHeaders[activePage] || pageHeaders.overview;

  const handleInspectAlert = (alert) => {
    if (alert.scanId) {
      selectScan(alert.scanId);
    }
    acknowledgeAlert(alert.id);
    setActivePage('findings');
  };

  return (
    <div 
      style={{
        display: 'flex',
        minHeight: '100vh',
        width: '100vw',
        backgroundColor: '#050D1F',
        position: 'relative',
        overflowX: 'hidden'
      }}
    >
      {/* Ambient Moving Cyber Background & Particles */}
      <AmbientCyberBackground />

      {/* Fixed Vertical Sidebar with 9 Functional Views & Version Indicator */}
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      {/* Main Viewport Content */}
      <main 
        style={{
          flex: 1,
          minWidth: 0,
          padding: '24px 28px',
          overflowY: 'auto',
          maxHeight: '100vh',
          position: 'relative',
          zIndex: 10,
          boxSizing: 'border-box'
        }}
      >
        {/* Horizontal Header with Dynamic Title, Live Telemetry Status & Notifications */}
        <Header 
          title={currentHeader.title} 
          subtitle={currentHeader.subtitle} 
          setActivePage={setActivePage}
        />

        {/* 9 Functional View Pages with Individual Error Boundaries */}
        {activePage === 'overview' && <SecurityOverview setActivePage={setActivePage} />}
        {activePage === 'new_scan' && <NewSecurityScan setActivePage={setActivePage} />}
        {activePage === 'history' && <ScanHistory setActivePage={setActivePage} />}
        {activePage === 'findings' && <VulnerabilityFindings setActivePage={setActivePage} />}
        {activePage === 'ai_analysis' && <AiSecurityAnalysis setActivePage={setActivePage} />}
        {activePage === 'retesting' && <RetestingVerification setActivePage={setActivePage} />}
        {activePage === 'notifications' && <NotificationsView setActivePage={setActivePage} />}
        {activePage === 'reports' && <Reports setActivePage={setActivePage} />}
        {activePage === 'settings' && <SettingsView setActivePage={setActivePage} />}

        {/* Footer with Visible Build Identity */}
        <footer
          style={{
            marginTop: '36px',
            paddingTop: '16px',
            borderTop: '1px solid rgba(15, 47, 78, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            color: '#6482A6',
          }}
        >
          <div>
            <span>API Sentinel | Frontend Build: </span>
            <strong className="font-mono-code" style={{ color: '#00E5FF' }}>v1.2.0-phase5-prod</strong>
            <span style={{ margin: '0 8px' }}>•</span>
            <span>Master Workspace: <code style={{ color: '#8AA4C8' }}>C:\PROJECTS\api-sentinel</code></span>
          </div>
          <div>
            <span>Backend: <strong style={{ color: '#22C55E' }}>FastAPI 1.0.0</strong></span>
            <span style={{ margin: '0 8px' }}>•</span>
            <span>AI: <strong style={{ color: '#C084FC' }}>Nemotron 3.5</strong></span>
          </div>
        </footer>
      </main>

      {/* In-App Critical Vulnerability Alert Popup Modal */}
      {activePopupAlert && (
        <CriticalAlertModal
          alert={activePopupAlert}
          onAcknowledge={() => acknowledgeAlert(activePopupAlert.id)}
          onInspect={handleInspectAlert}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary title="API Sentinel Application Error">
      <ScanProvider>
        <AppContent />
      </ScanProvider>
    </ErrorBoundary>
  );
}
