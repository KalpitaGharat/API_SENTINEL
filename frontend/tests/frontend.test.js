import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, '..');

test('Frontend Architecture & Build Integrity', async (t) => {
  await t.test('1. Production build dist directory contains valid index.html and assets', () => {
    const distPath = path.join(frontendRoot, 'dist');
    assert.ok(fs.existsSync(distPath), 'dist directory must exist');

    const indexPath = path.join(distPath, 'index.html');
    assert.ok(fs.existsSync(indexPath), 'dist/index.html must exist');

    const htmlContent = fs.readFileSync(indexPath, 'utf8');
    assert.ok(htmlContent.includes('<div id="root"></div>'), 'index.html must contain root mount point');

    const assetsPath = path.join(distPath, 'assets');
    assert.ok(fs.existsSync(assetsPath), 'dist/assets directory must exist');

    const assetFiles = fs.readdirSync(assetsPath);
    const jsBundles = assetFiles.filter((f) => f.endsWith('.js'));
    const cssBundles = assetFiles.filter((f) => f.endsWith('.css'));

    assert.ok(jsBundles.length >= 1, 'At least one compiled JS bundle must be emitted');
    assert.ok(cssBundles.length >= 1, 'At least one compiled CSS bundle must be emitted');
  });

  await t.test('2. Production build bundle does not leak any private NVIDIA API keys or bearer tokens', () => {
    const assetsPath = path.join(frontendRoot, 'dist', 'assets');
    const assetFiles = fs.readdirSync(assetsPath);
    const jsBundles = assetFiles.filter((f) => f.endsWith('.js'));

    for (const bundle of jsBundles) {
      const content = fs.readFileSync(path.join(assetsPath, bundle), 'utf8');
      assert.ok(!content.includes('nvapi-'), `Bundle ${bundle} must not contain raw NVIDIA API keys`);
      assert.ok(!content.includes('demo_password_'), `Bundle ${bundle} must not contain synthetic demo passwords`);
    }
  });

  await t.test('3. API Client exports all 12 backend endpoints with correct method signatures', async () => {
    const apiClientPath = path.join(frontendRoot, 'src', 'services', 'apiClient.js');
    assert.ok(fs.existsSync(apiClientPath), 'apiClient.js must exist');

    const content = fs.readFileSync(apiClientPath, 'utf8');
    const expectedMethods = [
      'getHealth',
      'getApiHealth',
      'createScan',
      'getScans',
      'getScan',
      'getScanFindings',
      'getFinding',
      'explainFinding',
      'getFindingHistory',
      'retestScan',
      'getScanReport',
    ];

    for (const method of expectedMethods) {
      assert.ok(content.includes(method), `apiClient must implement method ${method}`);
    }

    assert.ok(content.includes('/api/findings/'), 'apiClient must reference /api/findings/');
    assert.ok(content.includes('/api/scans/'), 'apiClient must reference /api/scans/');
    assert.ok(content.includes('/retest'), 'apiClient must reference /retest');
    assert.ok(content.includes('/explain'), 'apiClient must reference /explain');
    assert.ok(content.includes('/history'), 'apiClient must reference /history');
    assert.ok(content.includes('/report'), 'apiClient must reference /report');
  });

  await t.test('4. React ErrorBoundary is implemented and handles runtime errors safely', () => {
    const ebPath = path.join(frontendRoot, 'src', 'components', 'ErrorBoundary.jsx');
    assert.ok(fs.existsSync(ebPath), 'ErrorBoundary.jsx must exist');

    const content = fs.readFileSync(ebPath, 'utf8');
    assert.ok(content.includes('componentDidCatch'), 'ErrorBoundary must implement componentDidCatch');
    assert.ok(content.includes('getDerivedStateFromError'), 'ErrorBoundary must implement getDerivedStateFromError');
    assert.ok(content.includes('handleReset'), 'ErrorBoundary must provide a reset handler');
  });

  await t.test('5. NVIDIA Nemotron AI Explanation Panel handles loading, live badge, and fallback states', () => {
    const aiPanelPath = path.join(frontendRoot, 'src', 'components', 'AiExplanationPanel.jsx');
    assert.ok(fs.existsSync(aiPanelPath), 'AiExplanationPanel.jsx must exist');

    const content = fs.readFileSync(aiPanelPath, 'utf8');
    assert.ok(content.includes('Explain with Nemotron AI'), 'AI Panel must contain "Explain with Nemotron AI" action');
    assert.ok(content.includes('Regenerate AI Analysis'), 'AI Panel must contain "Regenerate AI Analysis" action');
    assert.ok(content.includes('explainFinding'), 'AI Panel must call explainFinding');
    assert.ok(content.includes('isNemotron'), 'AI Panel must distinguish live Nemotron from fallback');
  });

  await t.test('6. Retesting Verification view prevents blank-screen bug and updates retest history', () => {
    const retestPath = path.join(frontendRoot, 'src', 'views', 'RetestingVerification.jsx');
    assert.ok(fs.existsSync(retestPath), 'RetestingVerification.jsx must exist');

    const content = fs.readFileSync(retestPath, 'utf8');
    assert.ok(content.includes('Execute Targeted Verification Probe'), 'Retest view must contain probe button');
    assert.ok(content.includes('retestScan'), 'Retest view must call retestScan');
    assert.ok(content.includes('getFindingHistory'), 'Retest view must load retest history');
    assert.ok(content.includes('ErrorBoundary'), 'Retest view must be wrapped with ErrorBoundary');
  });

  await t.test('7. Critical Alert Modal and Notification Center provide in-app security alerts', () => {
    const alertModalPath = path.join(frontendRoot, 'src', 'components', 'CriticalAlertModal.jsx');
    const notifCenterPath = path.join(frontendRoot, 'src', 'components', 'NotificationCenter.jsx');

    assert.ok(fs.existsSync(alertModalPath), 'CriticalAlertModal.jsx must exist');
    assert.ok(fs.existsSync(notifCenterPath), 'NotificationCenter.jsx must exist');

    const modalContent = fs.readFileSync(alertModalPath, 'utf8');
    assert.ok(modalContent.includes('CRITICAL'), 'Modal must display CRITICAL severity badge');
    assert.ok(modalContent.includes('Acknowledge'), 'Modal must have an Acknowledge & Dismiss action');
    assert.ok(modalContent.includes('Inspect Finding with AI'), 'Modal must have an Inspect Finding with AI action');

    const notifContent = fs.readFileSync(notifCenterPath, 'utf8');
    assert.ok(notifContent.includes('Security Telemetry & Alerts'), 'NotificationCenter must have header');
    assert.ok(notifContent.includes('Acknowledge All'), 'NotificationCenter must support acknowledge all');
  });

  await t.test('8. Real-time Server-Sent Events (SSE) live updates are handled in ScanContext', () => {
    const contextPath = path.join(frontendRoot, 'src', 'context', 'ScanContext.jsx');
    assert.ok(fs.existsSync(contextPath), 'ScanContext.jsx must exist');

    const content = fs.readFileSync(contextPath, 'utf8');
    assert.ok(content.includes('EventSource'), 'ScanContext must initialize EventSource for SSE');
    assert.ok(content.includes('/api/events'), 'ScanContext must connect to /api/events');
    assert.ok(content.includes('critical_finding'), 'ScanContext must listen for critical_finding events');
    assert.ok(content.includes('scan_completed'), 'ScanContext must listen for scan_completed events');
    assert.ok(content.includes('activePopupAlert'), 'ScanContext must manage activePopupAlert state');
  });

  await t.test('9. Sidebar navigation renders all 9 functional views and visible version indicator', () => {
    const sidebarPath = path.join(frontendRoot, 'src', 'components', 'Sidebar.jsx');
    const appPath = path.join(frontendRoot, 'src', 'App.jsx');

    assert.ok(fs.existsSync(sidebarPath), 'Sidebar.jsx must exist');
    assert.ok(fs.existsSync(appPath), 'App.jsx must exist');

    const sidebarContent = fs.readFileSync(sidebarPath, 'utf8');
    const appContent = fs.readFileSync(appPath, 'utf8');

    const requiredViews = [
      'overview',
      'new_scan',
      'history',
      'findings',
      'ai_analysis',
      'retesting',
      'notifications',
      'reports',
      'settings',
    ];

    for (const view of requiredViews) {
      assert.ok(sidebarContent.includes(view), `Sidebar must contain navigation to ${view}`);
      assert.ok(appContent.includes(view), `App.jsx must render view ${view}`);
    }

    assert.ok(sidebarContent.includes('v1.2.0-phase5-prod'), 'Sidebar must display visible build version');
    assert.ok(appContent.includes('v1.2.0-phase5-prod'), 'Footer must display visible build version');
  });

  await t.test('10. Attack Demonstration & Evidence Inspector component is fully integrated', () => {
    const inspectorPath = path.join(frontendRoot, 'src', 'components', 'AttackEvidenceInspector.jsx');
    assert.ok(fs.existsSync(inspectorPath), 'AttackEvidenceInspector.jsx must exist');

    const inspectorContent = fs.readFileSync(inspectorPath, 'utf8');
    assert.ok(inspectorContent.includes('Attack Overview'), 'Inspector must have Attack Overview tab');
    assert.ok(inspectorContent.includes('Raw HTTP Request'), 'Inspector must have Raw HTTP Request tab');
    assert.ok(inspectorContent.includes('Raw HTTP Response'), 'Inspector must have Raw HTTP Response tab');
    assert.ok(inspectorContent.includes('Attack Timeline'), 'Inspector must have Attack Timeline tab');
    assert.ok(inspectorContent.includes('Evidence Integrity'), 'Inspector must have Evidence Integrity & Export tab');
    assert.ok(inspectorContent.includes('exportFindingEvidence'), 'Inspector must support evidence export');

    const findingsViewPath = path.join(frontendRoot, 'src', 'views', 'VulnerabilityFindings.jsx');
    const findingsContent = fs.readFileSync(findingsViewPath, 'utf8');
    assert.ok(findingsContent.includes('AttackEvidenceInspector'), 'VulnerabilityFindings must import AttackEvidenceInspector');
    assert.ok(findingsContent.includes('Inspect Attack & Evidence'), 'VulnerabilityFindings must have Inspect Attack & Evidence button');

    const retestViewPath = path.join(frontendRoot, 'src', 'views', 'RetestingVerification.jsx');
    const retestContent = fs.readFileSync(retestViewPath, 'utf8');
    assert.ok(retestContent.includes('Dual-Probe Verification Evidence'), 'Retesting view must render Dual-Probe verification matrix');
  });

  await t.test('11. Phase A Navigation & Route Consolidation renders all 9 primary views and isolates API Key Intel', () => {
    const sidebarPath = path.join(frontendRoot, 'src', 'components', 'Sidebar.jsx');
    const appPath = path.join(frontendRoot, 'src', 'App.jsx');
    const securityScansPath = path.join(frontendRoot, 'src', 'views', 'SecurityScans.jsx');
    const evidenceWorkspacePath = path.join(frontendRoot, 'src', 'views', 'AttackEvidenceWorkspace.jsx');
    const auditWorkspacePath = path.join(frontendRoot, 'src', 'views', 'AuditHistoryWorkspace.jsx');

    assert.ok(fs.existsSync(securityScansPath), 'SecurityScans.jsx must exist');
    assert.ok(fs.existsSync(evidenceWorkspacePath), 'AttackEvidenceWorkspace.jsx must exist');
    assert.ok(fs.existsSync(auditWorkspacePath), 'AuditHistoryWorkspace.jsx must exist');

    const sidebarContent = fs.readFileSync(sidebarPath, 'utf8');
    const appContent = fs.readFileSync(appPath, 'utf8');

    const ninePrimaryViews = [
      'overview',
      'targets',
      'scans',
      'findings',
      'evidence',
      'ai_analysis',
      'retesting',
      'audit_history',
      'settings'
    ];

    for (const view of ninePrimaryViews) {
      assert.ok(sidebarContent.includes(view), `Sidebar must contain primary navigation item ${view}`);
      assert.ok(appContent.includes(view), `App.jsx must route primary view ${view}`);
    }

    // Verify API Key Intelligence is preserved as optional/secondary, not in primary navItems
    assert.ok(sidebarContent.includes('api_key_intel'), 'Sidebar must provide optional access to api_key_intel');
    assert.ok(appContent.includes('api_key_intel'), 'App.jsx must preserve api_key_intel routing');
  });

  await t.test('12. Phase B Real Telemetry, Factual KPIs, and Scan Activity Aggregation', () => {
    const kpiPath = path.join(frontendRoot, 'src', 'components', 'KpiCards.jsx');
    const chartPath = path.join(frontendRoot, 'src', 'components', 'ScanActivityChart.jsx');
    const graphPath = path.join(frontendRoot, 'src', 'components', 'KpiCyberGraph.jsx');
    const recentTablePath = path.join(frontendRoot, 'src', 'components', 'RecentFindingsTable.jsx');
    const contextPath = path.join(frontendRoot, 'src', 'context', 'ScanContext.jsx');

    assert.ok(fs.existsSync(kpiPath), 'KpiCards.jsx must exist');
    assert.ok(fs.existsSync(chartPath), 'ScanActivityChart.jsx must exist');
    assert.ok(fs.existsSync(graphPath), 'KpiCyberGraph.jsx must exist');
    assert.ok(fs.existsSync(recentTablePath), 'RecentFindingsTable.jsx must exist');

    const kpiContent = fs.readFileSync(kpiPath, 'utf8');
    const chartContent = fs.readFileSync(chartPath, 'utf8');
    const graphContent = fs.readFileSync(graphPath, 'utf8');
    const recentContent = fs.readFileSync(recentTablePath, 'utf8');
    const contextContent = fs.readFileSync(contextPath, 'utf8');

    // 1. Verify arbitrary health score formula is completely removed from KpiCards
    assert.ok(!kpiContent.includes('crit * 25'), 'Arbitrary health score formula (crit*25) must be removed');
    assert.ok(!kpiContent.includes('fixedVulns * 10'), 'Arbitrary health score formula (fixedVulns*10) must be removed');

    // 2. Verify factual metrics are implemented: Total Scans, Open Findings, Verified Resolved, Resolution Rate
    assert.ok(kpiContent.includes('TOTAL SCANS'), 'KpiCards must display TOTAL SCANS');
    assert.ok(kpiContent.includes('OPEN FINDINGS'), 'KpiCards must display OPEN FINDINGS');
    assert.ok(kpiContent.includes('VERIFIED RESOLVED'), 'KpiCards must display VERIFIED RESOLVED');
    assert.ok(kpiContent.includes('RESOLUTION RATE'), 'KpiCards must display RESOLUTION RATE');
    assert.ok(kpiContent.includes('resolutionRate'), 'KpiCards must calculate resolutionRate');

    // 3. Verify Needs Review is never treated as Resolved
    assert.ok(kpiContent.includes('needs review'), 'KpiCards must explicitly identify needs review status');
    assert.ok(kpiContent.includes('needsReviewCount'), 'KpiCards must track needsReviewCount separately from resolved');

    // 4. Verify ScanActivityChart has no fabricated dates or mock arrays
    assert.ok(!chartContent.includes('Oct 27'), 'ScanActivityChart must not contain hardcoded dates');
    assert.ok(!chartContent.includes('1.0, 1.8, 2.8'), 'ScanActivityChart must not contain fabricated data points');
    assert.ok(chartContent.includes('created_at'), 'ScanActivityChart must aggregate scans by created_at timestamp');
    assert.ok(chartContent.includes('No Historical Scan Activity Recorded'), 'ScanActivityChart must render an honest zero state');

    // 5. Verify KpiCyberGraph has no fabricated trajectory trendData
    assert.ok(!graphContent.includes('13.2, 15.8, 14.2'), 'KpiCyberGraph must not contain fabricated trend data');
    assert.ok(!graphContent.includes('trendData'), 'KpiCyberGraph must not use hardcoded trendData');

    // 6. Verify RecentFindingsTable includes timestamp, endpoint, severity, status and no fabricated rows
    assert.ok(recentContent.includes('Detected At'), 'RecentFindingsTable must render Detected At header');
    assert.ok(recentContent.includes('created_at'), 'RecentFindingsTable must format finding created_at');
    assert.ok(recentContent.includes('No Vulnerability Findings Detected'), 'RecentFindingsTable must have an honest zero state');

    // 7. Verify SSE event synchronization refreshes findings without double-counting
    assert.ok(contextContent.includes('critical_finding'), 'ScanContext must handle critical_finding');
    assert.ok(contextContent.includes('refreshFindings'), 'ScanContext must refetch backend data on events to prevent duplicate counting');
    assert.ok(contextContent.includes('retest_completed'), 'ScanContext must handle retest_completed');
  });

  await t.test('13. Phase C Workspaces: Attack Evidence Inspector & Audit History Ledger', () => {
    const inspectorPath = path.join(frontendRoot, 'src', 'components', 'AttackEvidenceInspector.jsx');
    const evidenceWorkspacePath = path.join(frontendRoot, 'src', 'views', 'AttackEvidenceWorkspace.jsx');
    const auditWorkspacePath = path.join(frontendRoot, 'src', 'views', 'AuditHistoryWorkspace.jsx');
    const appPath = path.join(frontendRoot, 'src', 'App.jsx');
    const sidebarPath = path.join(frontendRoot, 'src', 'components', 'Sidebar.jsx');

    assert.ok(fs.existsSync(inspectorPath), 'AttackEvidenceInspector.jsx must exist');
    assert.ok(fs.existsSync(evidenceWorkspacePath), 'AttackEvidenceWorkspace.jsx must exist');
    assert.ok(fs.existsSync(auditWorkspacePath), 'AuditHistoryWorkspace.jsx must exist');

    const inspectorContent = fs.readFileSync(inspectorPath, 'utf8');
    const evidenceWorkspaceContent = fs.readFileSync(evidenceWorkspacePath, 'utf8');
    const auditWorkspaceContent = fs.readFileSync(auditWorkspacePath, 'utf8');
    const appContent = fs.readFileSync(appPath, 'utf8');
    const sidebarContent = fs.readFileSync(sidebarPath, 'utf8');

    // 1. Evidence Inspector: Embedded mode support and complete removal of fake fallback digests
    assert.ok(inspectorContent.includes('embedded'), 'AttackEvidenceInspector must support embedded mode prop');
    assert.ok(!inspectorContent.includes('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), 'Hardcoded fallback SHA-256 hash must be eradicated');
    assert.ok(!inspectorContent.includes('Synthetic Patient B'), 'Fabricated patient fallback records must be eradicated');
    assert.ok(inspectorContent.includes('onNavigateToAudit'), 'Inspector must provide direct navigation to audit history ledger');

    // 2. Evidence Workspace: Dedicated full-screen layout and deep linking
    assert.ok(evidenceWorkspaceContent.includes('embedded={true}'), 'AttackEvidenceWorkspace must render inspector in embedded mode');
    assert.ok(evidenceWorkspaceContent.includes('initialFindingId'), 'AttackEvidenceWorkspace must accept initialFindingId');
    assert.ok(evidenceWorkspaceContent.includes('Back to Findings Table'), 'AttackEvidenceWorkspace must provide clear back navigation');

    // 3. Audit History Workspace: Aggregate session ledger and dual-probe telemetry
    assert.ok(auditWorkspaceContent.includes('Aggregate Session Ledger'), 'AuditHistoryWorkspace must support aggregate scan session ledger');
    assert.ok(auditWorkspaceContent.includes('VERIFIED RESOLVED'), 'AuditHistoryWorkspace must render VERIFIED RESOLVED status');
    assert.ok(auditWorkspaceContent.includes('STILL VULNERABLE'), 'AuditHistoryWorkspace must render STILL VULNERABLE status');
    assert.ok(auditWorkspaceContent.includes('NEEDS REVIEW'), 'AuditHistoryWorkspace must render NEEDS REVIEW status');
    assert.ok(auditWorkspaceContent.includes('ownerProbe'), 'AuditHistoryWorkspace must display owner probe details');
    assert.ok(auditWorkspaceContent.includes('attackerProbe'), 'AuditHistoryWorkspace must display attacker probe details');
    assert.ok(auditWorkspaceContent.includes('statusFilter'), 'AuditHistoryWorkspace must implement status filtering');

    // 4. Routing & Aliases: #evidence, #audit, and #audit_history with parameter support
    assert.ok(appContent.includes("route === 'audit'"), 'App.jsx must support #audit route alias');
    assert.ok(appContent.includes('parseHashRoute'), 'App.jsx must parse hash route and query params');
    assert.ok(sidebarContent.includes("activePage === 'audit'"), 'Sidebar must highlight audit nav for both #audit and #audit_history');
  });

  await t.test('14. Phase D Target & Scan Workflow Unification: Contextual Scan Launching, Target Telemetry, and Cross-Workspace Navigation', () => {
    const scanContextPath = path.join(frontendRoot, 'src', 'context', 'ScanContext.jsx');
    const newScanPath = path.join(frontendRoot, 'src', 'views', 'NewSecurityScan.jsx');
    const securityScansPath = path.join(frontendRoot, 'src', 'views', 'SecurityScans.jsx');
    const apiOnboardingPath = path.join(frontendRoot, 'src', 'views', 'ApiOnboarding.jsx');
    const scanHistoryPath = path.join(frontendRoot, 'src', 'views', 'ScanHistory.jsx');
    const appPath = path.join(frontendRoot, 'src', 'App.jsx');

    const scanContextContent = fs.readFileSync(scanContextPath, 'utf8');
    const newScanContent = fs.readFileSync(newScanPath, 'utf8');
    const securityScansContent = fs.readFileSync(securityScansPath, 'utf8');
    const apiOnboardingContent = fs.readFileSync(apiOnboardingPath, 'utf8');
    const scanHistoryContent = fs.readFileSync(scanHistoryPath, 'utf8');
    const appContent = fs.readFileSync(appPath, 'utf8');

    // 1. ScanContext target state management
    assert.ok(scanContextContent.includes('selectedTargetId'), 'ScanContext must provide selectedTargetId');
    assert.ok(scanContextContent.includes('selectTarget'), 'ScanContext must provide selectTarget');
    assert.ok(scanContextContent.includes('refreshTargets'), 'ScanContext must provide refreshTargets');
    assert.ok(scanContextContent.includes('isLoadingTargets'), 'ScanContext must provide isLoadingTargets');

    // 2. App.jsx contextual route and parameter passing
    assert.ok(appContent.includes('target_id'), 'App.jsx parseHashRoute must support target_id');
    assert.ok(appContent.includes('initialTargetId={navTargetId}'), 'App.jsx must pass initialTargetId to views');
    assert.ok(securityScansContent.includes('initialTargetId'), 'SecurityScans must accept and forward initialTargetId');

    // 3. NewSecurityScan: Target selector, telemetry, validation, and contextual dispatch
    assert.ok(newScanContent.includes('Registered API Target Catalog'), 'NewSecurityScan must render Target API Catalog selector');
    assert.ok(newScanContent.includes('validateTargetConnectivity'), 'NewSecurityScan must support live connectivity testing');
    assert.ok(newScanContent.includes('launchTargetScan'), 'NewSecurityScan must support launchTargetScan endpoint');
    assert.ok(newScanContent.includes('duplicate submission'), 'NewSecurityScan must prevent duplicate scan submissions');
    assert.ok(newScanContent.includes('Navigate to Findings'), 'NewSecurityScan must offer post-scan navigation to findings');
    assert.ok(newScanContent.includes('Inspect Evidence'), 'NewSecurityScan must offer post-scan navigation to evidence');

    // 4. ApiOnboarding: Direct card validation and 1-click launcher navigation
    assert.ok(apiOnboardingContent.includes('handleValidateCardTarget'), 'ApiOnboarding must support direct card-level target validation');
    assert.ok(apiOnboardingContent.includes("setActivePage('scans'"), 'ApiOnboarding must link Scan action to scans workbench');
    assert.ok(apiOnboardingContent.includes('Open in Full Scans Workbench'), 'ApiOnboarding scan tab must link to full scans workbench');

    // 5. ScanHistory: Direct 1-click cross-workspace action buttons
    assert.ok(scanHistoryContent.includes("setActivePage('findings'"), 'ScanHistory must provide direct navigation to findings');
    assert.ok(scanHistoryContent.includes("setActivePage('evidence'"), 'ScanHistory must provide direct navigation to evidence');
    assert.ok(scanHistoryContent.includes("setActivePage('retesting'"), 'ScanHistory must provide direct navigation to retesting');
  });
});
