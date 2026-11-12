import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AmbientCyberBackground from './components/AmbientCyberBackground';
import CriticalAlertModal from './components/CriticalAlertModal';
import SecurityOverview from './views/SecurityOverview';
import SecurityScans from './views/SecurityScans';
import NewSecurityScan from './views/NewSecurityScan';
import ScanHistory from './views/ScanHistory';
import VulnerabilityFindings from './views/VulnerabilityFindings';
import AttackEvidenceWorkspace from './views/AttackEvidenceWorkspace';
import AiSecurityAnalysis from './views/AiSecurityAnalysis';
import ApiKeyIntelligence from './views/ApiKeyIntelligence';
import RetestingVerification from './views/RetestingVerification';
import AuditHistoryWorkspace from './views/AuditHistoryWorkspace';
import NotificationsView from './views/NotificationsView';
import Reports from './views/Reports';
import SettingsView from './views/SettingsView';
import ApiOnboarding from './views/ApiOnboarding';
import { ScanProvider, useScanContext } from './context/ScanContext';
import ErrorBoundary from './components/ErrorBoundary';

function parseHashRoute() {
  const raw = (window.location.hash || '').replace('#', '');
  const [pathPart, queryPart] = raw.split('?');
  const params = new URLSearchParams(queryPart || '');

  let route = (pathPart || 'overview').toLowerCase();
  if (route === 'audit') route = 'audit_history';
  if (route === 'onboarding') route = 'targets';

  const validPages = [
    'overview', 'targets', 'onboarding', 'scans', 'new_scan', 'history',
    'findings', 'evidence', 'ai_analysis', 'retesting', 'audit_history', 'audit',
    'settings', 'api_key_intel', 'notifications', 'reports'
  ];

  if (!validPages.includes(route)) {
    route = 'overview';
  }

  return {
    route,
    findingId: params.get('finding_id') || params.get('id') || null,
    scanId: params.get('scan_id') || null,
    targetId: params.get('target_id') || null,
    tab: params.get('tab') || null,
  };
}

function AppContent() {
  const initial = parseHashRoute();
  const [activePage, setActivePageState] = useState(initial.route);
  const [navFindingId, setNavFindingId] = useState(initial.findingId);
  const [navTargetId, setNavTargetId] = useState(initial.targetId);
  const [navTab, setNavTab] = useState(initial.tab);
  const { activePopupAlert, acknowledgeAlert, selectScan, selectFinding, selectTarget } = useScanContext();

  // If initial URL had finding_id, scan_id, or target_id, sync to context on boot
  useEffect(() => {
    if (initial.scanId) {
      selectScan(initial.scanId);
    }
    if (initial.findingId) {
      selectFinding(initial.findingId, initial.scanId);
    }
    if (initial.targetId) {
      selectTarget(initial.targetId);
    }
  }, []);

  const setActivePage = (page, options = {}) => {
    let targetPage = page;
    if (page === 'audit') targetPage = 'audit_history';
    if (page === 'onboarding') targetPage = 'targets';

    setActivePageState(targetPage);

    const fId = options?.findingId || options?.id || null;
    const sId = options?.scanId || null;
    const tId = options?.targetId || null;
    const tab = options?.tab || null;

    if (fId) {
      setNavFindingId(fId);
      selectFinding(fId, sId);
    }
    if (tId) {
      setNavTargetId(tId);
      selectTarget(tId);
    }
    if (tab) {
      setNavTab(tab);
    }

    try {
      const params = new URLSearchParams();
      if (fId) params.append('finding_id', fId);
      if (sId) params.append('scan_id', sId);
      if (tId) params.append('target_id', tId);
      if (tab) params.append('tab', tab);
      const queryStr = params.toString() ? `?${params.toString()}` : '';
      const hashPage = (targetPage === 'audit_history') ? 'audit' : targetPage;
      window.location.hash = `${hashPage}${queryStr}`;
    } catch (_) {}
  };

  useEffect(() => {
    const handleHashChange = () => {
      const parsed = parseHashRoute();
      if (parsed.route && parsed.route !== activePage) {
        setActivePageState(parsed.route);
      }
      if (parsed.findingId) {
        setNavFindingId(parsed.findingId);
        selectFinding(parsed.findingId, parsed.scanId);
      }
      if (parsed.targetId) {
        setNavTargetId(parsed.targetId);
        selectTarget(parsed.targetId);
      }
      if (parsed.tab) {
        setNavTab(parsed.tab);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [activePage, selectFinding, selectTarget]);

  const pageHeaders = {
    overview: {
      title: 'Security Overview',
      subtitle: 'Real-time telemetry of your API security posture, findings, and scan activity.'
    },
    targets: {
      title: 'API Targets & Inventory',
      subtitle: 'Register target APIs, import OpenAPI/Swagger specifications, and configure dual-principal authorization testing.'
    },
    onboarding: {
      title: 'API Targets & Inventory',
      subtitle: 'Register target APIs, import OpenAPI/Swagger specifications, and configure dual-principal authorization testing.'
    },
    scans: {
      title: 'Security Scans',
      subtitle: 'Execute automated security scans, monitor live probe progress, and review historical audit sessions.'
    },
    new_scan: {
      title: 'Security Scans — New Scan',
      subtitle: 'Configure target API boundaries, scan profiles, and launch automated security audits.'
    },
    history: {
      title: 'Security Scans — Historical Registry',
      subtitle: 'Complete chronological audit trail of all security scans, test runs, and regression probes.'
    },
    findings: {
      title: 'Vulnerability Findings',
      subtitle: 'Explore detected security vulnerabilities, technical HTTP evidence, and NVIDIA Nemotron AI explanations.'
    },
    evidence: {
      title: 'Attack Evidence Inspector',
      subtitle: 'Forensic inspection of HTTP telemetry, dual-principal exploit flows, and RFC 8785 SHA-256 evidence integrity.'
    },
    ai_analysis: {
      title: 'NVIDIA Nemotron AI Security Analysis',
      subtitle: 'Deep explainable intelligence: contextual vulnerability breakdowns, simulated threat scenarios, and remediation code.'
    },
    retesting: {
      title: 'Verification & Retesting',
      subtitle: 'Automated targeted regression probes to mathematically verify security remediation on patched endpoints.'
    },
    audit_history: {
      title: 'Audit History',
      subtitle: 'Chronological, immutable ledger of all verification retests, probe telemetry, and verified fixes.'
    },
    audit: {
      title: 'Audit History',
      subtitle: 'Chronological, immutable ledger of all verification retests, probe telemetry, and verified fixes.'
    },
    settings: {
      title: 'System Settings & Infrastructure',
      subtitle: 'FastAPI core node status, SQLite persistence health, and real-time Server-Sent Events (SSE) telemetry.'
    },
    api_key_intel: {
      title: 'API Key Intelligence & Detection Benchmark',
      subtitle: '10,000-sample benchmark dataset, provider format analysis, and real-time detection accuracy evaluation.'
    },
    notifications: {
      title: 'Security Notifications & Telemetry Feed',
      subtitle: 'Real-time stream of discovered vulnerabilities, scan lifecycle events, and audit logs.'
    },
    reports: {
      title: 'Security & Compliance Reports',
      subtitle: 'Export executive summaries, OWASP API Top 10 compliance scorecards, and audit logs.'
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

      {/* Fixed Vertical Sidebar with 9 Primary Sections & Version Indicator */}
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
        {/* Horizontal Header with Dynamic Title, Live Telemetry Status & Notifications Drawer */}
        <Header 
          title={currentHeader.title} 
          subtitle={currentHeader.subtitle} 
          setActivePage={setActivePage}
        />

        {/* 9 Primary Functional View Pages with Individual Error Boundaries */}
        {activePage === 'overview' && <SecurityOverview setActivePage={setActivePage} />}
        {(activePage === 'targets' || activePage === 'onboarding') && <ApiOnboarding setActivePage={setActivePage} initialTargetId={navTargetId} />}
        {activePage === 'scans' && <SecurityScans setActivePage={setActivePage} initialTargetId={navTargetId} initialTab={navTab || 'new'} />}
        {activePage === 'new_scan' && <SecurityScans setActivePage={setActivePage} initialTab="new" initialTargetId={navTargetId} />}
        {activePage === 'history' && <SecurityScans setActivePage={setActivePage} initialTab="history" />}
        {activePage === 'findings' && <VulnerabilityFindings setActivePage={setActivePage} />}
        {activePage === 'evidence' && <AttackEvidenceWorkspace setActivePage={setActivePage} initialFindingId={navFindingId} />}
        {activePage === 'ai_analysis' && <AiSecurityAnalysis setActivePage={setActivePage} initialFindingId={navFindingId} />}
        {activePage === 'retesting' && <RetestingVerification setActivePage={setActivePage} initialFindingId={navFindingId} />}
        {(activePage === 'audit_history' || activePage === 'audit') && <AuditHistoryWorkspace setActivePage={setActivePage} initialFindingId={navFindingId} />}
        {activePage === 'settings' && <SettingsView setActivePage={setActivePage} />}

        {/* Preserved Secondary & Legacy Views */}
        {activePage === 'api_key_intel' && <ApiKeyIntelligence setActivePage={setActivePage} />}
        {activePage === 'notifications' && <NotificationsView setActivePage={setActivePage} />}
        {activePage === 'reports' && <Reports setActivePage={setActivePage} />}

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
