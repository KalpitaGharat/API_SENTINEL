import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import apiClient, { ApiError } from '../services/apiClient';

const ScanContext = createContext(null);

const STORAGE_KEY_ACK = 'apisentinel_acknowledged_alerts';

function getStoredAcknowledgedIds() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_ACK);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function persistAcknowledgedId(id) {
  try {
    const current = getStoredAcknowledgedIds();
    current.add(id);
    localStorage.setItem(STORAGE_KEY_ACK, JSON.stringify(Array.from(current)));
  } catch (err) {
    console.warn('[ScanContext] Failed to persist acknowledged alert:', err);
  }
}

export function ScanProvider({ children }) {
  const [scans, setScans] = useState([]);
  const [selectedScanId, setSelectedScanId] = useState(null);
  const [activeScan, setActiveScan] = useState(null);
  const [findings, setFindings] = useState([]);
  const [allFindings, setAllFindings] = useState([]);
  const [selectedFindingId, setSelectedFindingId] = useState(null);
  const [targets, setTargets] = useState([]);
  const [selectedTargetId, setSelectedTargetId] = useState(null);
  const [isLoadingScans, setIsLoadingScans] = useState(false);
  const [isLoadingFindings, setIsLoadingFindings] = useState(false);
  const [isLoadingTargets, setIsLoadingTargets] = useState(false);
  const [backendConnected, setBackendConnected] = useState(true);
  const [backendError, setBackendError] = useState(null);
  const [sseStatus, setSseStatus] = useState('disconnected'); // connected, connecting, disconnected

  // Security Alert & Notification Center State
  const [notifications, setNotifications] = useState([]);
  const [activePopupAlert, setActivePopupAlert] = useState(null);
  const acknowledgedIdsRef = useRef(getStoredAcknowledgedIds());

  // Check health and load recent scans
  const refreshScans = useCallback(async (autoSelectScanId = null) => {
    setIsLoadingScans(true);
    setBackendError(null);
    try {
      const data = await apiClient.getScans({ limit: 50 });
      const items = data?.items || [];
      setScans(items);
      setBackendConnected(true);

      // Auto-select latest or requested scan
      if (items.length > 0) {
        setSelectedScanId((prev) => {
          if (autoSelectScanId && items.some((s) => s.id === autoSelectScanId)) {
            return autoSelectScanId;
          }
          if (!prev || !items.some((s) => s.id === prev)) {
            return items[0].id;
          }
          return prev;
        });
      }

      // Load cumulative findings across all scans for aggregate distribution
      try {
        let cumulative = [];
        const all = await apiClient.getAllFindings().catch(() => null);
        if (Array.isArray(all) && all.length > 0) {
          cumulative = all;
        } else if (items.length > 0) {
          const findingsPromises = items.map((s) =>
            apiClient.getScanFindings(s.id).catch(() => [])
          );
          const findingsArrays = await Promise.all(findingsPromises);
          const flattened = findingsArrays.flat();
          cumulative = Array.from(
            new Map(flattened.map((f) => [f.id, f])).values()
          );
        }
        setAllFindings(cumulative);
      } catch (aggErr) {
        console.warn('[ScanContext] Failed to aggregate cumulative findings:', aggErr);
      }
    } catch (err) {
      console.warn('[ScanContext] Failed to load scans from backend:', err);
      setBackendConnected(false);
      setBackendError(err.message);
    } finally {
      setIsLoadingScans(false);
    }
  }, []);

  // Check health and load registered API targets
  const refreshTargets = useCallback(async (autoSelectTargetId = null) => {
    setIsLoadingTargets(true);
    try {
      const data = await apiClient.getTargets({ limit: 50 });
      const items = data?.items || [];
      setTargets(items);
      if (items.length > 0) {
        setSelectedTargetId((prev) => {
          if (autoSelectTargetId && items.some((t) => t.id === autoSelectTargetId)) {
            return autoSelectTargetId;
          }
          if (!prev || !items.some((t) => t.id === prev)) {
            return items[0].id;
          }
          return prev;
        });
      }
    } catch (err) {
      console.warn('[ScanContext] Failed to load targets:', err);
    } finally {
      setIsLoadingTargets(false);
    }
  }, []);

  // When selectedScanId changes, load scan details and findings
  const refreshFindings = useCallback(async (scanId = selectedScanId) => {
    if (!scanId) {
      setActiveScan(null);
      setFindings([]);
      return;
    }

    setIsLoadingFindings(true);
    try {
      const [scanData, findingsData] = await Promise.all([
        apiClient.getScan(scanId).catch(() => null),
        apiClient.getScanFindings(scanId).catch(() => []),
      ]);

      if (scanData) {
        setActiveScan(scanData);
      }
      const verifiedFindings = Array.isArray(findingsData) ? findingsData : [];
      setFindings(verifiedFindings);
      setBackendConnected(true);

      // Inspect for unacknowledged critical findings and trigger in-app popup
      const unackCritical = verifiedFindings.find(
        (f) => (f.severity || '').toLowerCase() === 'critical' && 
               !acknowledgedIdsRef.current.has(f.id)
      );
      if (unackCritical && !activePopupAlert) {
        setActivePopupAlert({
          id: unackCritical.id,
          findingId: unackCritical.id,
          scanId: unackCritical.scan_id,
          vulnerability: unackCritical.vulnerability,
          endpoint: unackCritical.endpoint,
          severity: unackCritical.severity,
          category: unackCritical.category,
          description: unackCritical.description,
          timestamp: unackCritical.created_at,
        });
      }
    } catch (err) {
      console.warn(`[ScanContext] Failed to load findings for scan ${scanId}:`, err);
    } finally {
      setIsLoadingFindings(false);
    }
  }, [selectedScanId, activePopupAlert]);

  // Initial load
  useEffect(() => {
    refreshScans();
    refreshTargets();
  }, [refreshScans, refreshTargets]);

  // Auto-refresh findings when selected scan changes
  useEffect(() => {
    if (selectedScanId) {
      refreshFindings(selectedScanId);
    }
  }, [selectedScanId, refreshFindings]);

  // Select scan helper with immediate loading
  const selectScan = useCallback((scanId, autoRefresh = true) => {
    setSelectedScanId(scanId);
    if (autoRefresh && scanId) {
      refreshFindings(scanId);
    }
  }, [refreshFindings]);

  // Select finding helper with optional scan auto-selection
  const selectFinding = useCallback((findingId, scanId = null) => {
    if (scanId && scanId !== selectedScanId) {
      setSelectedScanId(scanId);
      refreshFindings(scanId);
    }
    setSelectedFindingId(findingId);
  }, [selectedScanId, refreshFindings]);

  // Select target helper
  const selectTarget = useCallback((targetId) => {
    setSelectedTargetId(targetId);
  }, []);

  const selectedTarget = (targets || []).find((t) => t.id === selectedTargetId) || (targets && targets[0]) || null;

  // Acknowledge an alert
  const acknowledgeAlert = useCallback((id) => {
    if (!id) return;
    persistAcknowledgedId(id);
    acknowledgedIdsRef.current.add(id);

    setNotifications((prev) =>
      prev.map((n) => (n.id === id || n.findingId === id ? { ...n, acknowledged: true } : n))
    );

    setActivePopupAlert((prev) => (prev?.id === id || prev?.findingId === id ? null : prev));
  }, []);

  // Acknowledge all alerts
  const acknowledgeAllAlerts = useCallback(() => {
    notifications.forEach((n) => {
      persistAcknowledgedId(n.id);
      if (n.findingId) persistAcknowledgedId(n.findingId);
      acknowledgedIdsRef.current.add(n.id);
    });
    setNotifications((prev) => prev.map((n) => ({ ...n, acknowledged: true })));
    setActivePopupAlert(null);
  }, [notifications]);

  // Dismiss popup without permanent acknowledge
  const dismissPopup = useCallback(() => {
    setActivePopupAlert(null);
  }, []);

  // Real-time Server-Sent Events (SSE) listener
  useEffect(() => {
    let eventSource = null;
    let reconnectTimeout = null;

    const connectSSE = () => {
      try {
        setSseStatus('connecting');
        const sseUrl = `${apiClient.baseUrl.replace(/\/+$/, '')}/api/events`;
        eventSource = new EventSource(sseUrl);

        eventSource.addEventListener('connected', (e) => {
          setSseStatus('connected');
          setBackendConnected(true);
        });

        eventSource.addEventListener('scan_created', (e) => {
          try {
            const data = JSON.parse(e.data);
            refreshScans(data.scan_id);
            setNotifications((prev) => [
              {
                id: `evt-${Date.now()}-${Math.random()}`,
                type: 'scan_created',
                title: 'Security Scan Initiated',
                message: `Scan started against ${data.target_url}`,
                scanId: data.scan_id,
                severity: 'info',
                timestamp: data.created_at || new Date().toISOString(),
                acknowledged: false,
              },
              ...prev.slice(0, 49),
            ]);
          } catch (err) {
            console.warn('[SSE] Failed to parse scan_created event:', err);
          }
        });

        eventSource.addEventListener('critical_finding', (e) => {
          try {
            const data = JSON.parse(e.data);
            const alertItem = {
              id: data.finding_id,
              findingId: data.finding_id,
              scanId: data.scan_id,
              vulnerability: data.vulnerability,
              endpoint: data.endpoint,
              severity: data.severity,
              category: data.category,
              description: data.description,
              timestamp: data.created_at || new Date().toISOString(),
              acknowledged: false,
            };

            setNotifications((prev) => [alertItem, ...prev.slice(0, 49)]);

            // Immediately refresh findings to update dashboard KPIs without duplicate counting
            if (data.scan_id) {
              refreshFindings(data.scan_id);
            }

            // If not previously acknowledged, show prominent popup modal immediately
            if (!acknowledgedIdsRef.current.has(data.finding_id)) {
              setActivePopupAlert(alertItem);
            }
          } catch (err) {
            console.warn('[SSE] Failed to parse critical_finding event:', err);
          }
        });

        eventSource.addEventListener('scan_completed', (e) => {
          try {
            const data = JSON.parse(e.data);
            refreshScans(data.scan_id);
            refreshFindings(data.scan_id);
            setNotifications((prev) => [
              {
                id: `evt-${Date.now()}-${Math.random()}`,
                type: 'scan_completed',
                title: 'Security Scan Completed',
                message: `Audit completed: ${data.total_findings} vulnerabilities detected.`,
                scanId: data.scan_id,
                severity: data.total_findings > 0 ? 'high' : 'info',
                timestamp: data.completed_at || new Date().toISOString(),
                acknowledged: false,
              },
              ...prev.slice(0, 49),
            ]);
          } catch (err) {
            console.warn('[SSE] Failed to parse scan_completed event:', err);
          }
        });

        eventSource.addEventListener('scan_failed', (e) => {
          try {
            const data = JSON.parse(e.data);
            refreshScans(data.scan_id);
            setNotifications((prev) => [
              {
                id: `evt-${Date.now()}-${Math.random()}`,
                type: 'scan_failed',
                title: 'Security Scan Failed',
                message: data.error || 'Security testing engine encountered an execution error.',
                scanId: data.scan_id,
                severity: 'critical',
                timestamp: new Date().toISOString(),
                acknowledged: false,
              },
              ...prev.slice(0, 49),
            ]);
          } catch (err) {
            console.warn('[SSE] Failed to parse scan_failed event:', err);
          }
        });

        eventSource.addEventListener('retest_completed', (e) => {
          try {
            const data = JSON.parse(e.data);
            refreshFindings(data.scan_id);
            refreshScans(data.scan_id);
            setNotifications((prev) => [
              {
                id: `evt-${Date.now()}-${Math.random()}`,
                type: 'retest_completed',
                title: 'Targeted Verification Completed',
                message: `Verification probe completed (${data.verified_count}/${data.total_retested} verified fixed).`,
                scanId: data.scan_id,
                severity: 'info',
                timestamp: data.retested_at || new Date().toISOString(),
                acknowledged: false,
              },
              ...prev.slice(0, 49),
            ]);
          } catch (err) {
            console.warn('[SSE] Failed to parse retest_completed event:', err);
          }
        });

        eventSource.onerror = (err) => {
          setSseStatus('disconnected');
          eventSource.close();
          // Auto-reconnect after 6 seconds
          reconnectTimeout = setTimeout(connectSSE, 6000);
        };
      } catch (err) {
        console.warn('[SSE] Could not establish EventSource:', err);
        setSseStatus('disconnected');
        reconnectTimeout = setTimeout(connectSSE, 10000);
      }
    };

    connectSSE();

    // Fallback heartbeat polling every 12s in case SSE is blocked by proxies
    const fallbackPoll = setInterval(() => {
      refreshScans();
    }, 12000);

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(fallbackPoll);
    };
  }, [refreshScans, refreshFindings]);

  const unreadAlertCount = notifications.filter((n) => !n.acknowledged).length;

  const contextValue = {
    scans,
    selectedScanId,
    activeScan,
    findings,
    allFindings,
    totalScansCount: (scans || []).length,
    totalVulnerabilitiesCount: (allFindings && allFindings.length > 0)
      ? allFindings.length
      : (scans || []).reduce((acc, s) => acc + (s.total_findings || s.vulnerabilities_found || 0), 0),
    selectedFindingId,
    targets,
    selectedTargetId,
    selectedTarget,
    isLoadingScans,
    isLoadingFindings,
    isLoadingTargets,
    backendConnected,
    backendError,
    sseStatus,
    notifications,
    unreadAlertCount,
    activePopupAlert,
    refreshScans,
    refreshFindings,
    refreshTargets,
    selectScan,
    setSelectedScanId,
    selectFinding,
    setSelectedFindingId,
    selectTarget,
    setSelectedTargetId,
    acknowledgeAlert,
    acknowledgeAllAlerts,
    dismissPopup,
    setActivePopupAlert,
  };

  return (
    <ScanContext.Provider value={contextValue}>
      {children}
    </ScanContext.Provider>
  );
}

export function useScanContext() {
  const ctx = useContext(ScanContext);
  if (!ctx) {
    throw new Error('useScanContext must be used within a ScanProvider');
  }
  return ctx;
}

export default ScanContext;
