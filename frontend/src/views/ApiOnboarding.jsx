import React, { useState, useEffect, useMemo } from 'react';
import { 
  Server, 
  Layers, 
  Globe, 
  Shield, 
  ShieldAlert, 
  Key, 
  Check, 
  AlertCircle, 
  FileCode, 
  Upload, 
  RefreshCw, 
  Trash2, 
  ExternalLink, 
  Play, 
  Eye, 
  EyeOff, 
  Search, 
  Filter, 
  Lock, 
  CheckCircle2, 
  ChevronRight, 
  Info, 
  AlertTriangle, 
  ArrowRight,
  Terminal,
  Database,
  PlusCircle,
  HelpCircle
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

const DEMO_API_URL = 'http://127.0.0.1:8001';
const DEMO_SPEC_URL = 'http://127.0.0.1:8001/openapi.json';

const METHOD_COLORS = {
  GET: { bg: 'rgba(59, 130, 246, 0.15)', text: '#60A5FA', border: 'rgba(59, 130, 246, 0.4)' },
  POST: { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ADE80', border: 'rgba(34, 197, 94, 0.4)' },
  PUT: { bg: 'rgba(245, 158, 11, 0.15)', text: '#FBBF24', border: 'rgba(245, 158, 11, 0.4)' },
  PATCH: { bg: 'rgba(168, 85, 247, 0.15)', text: '#C084FC', border: 'rgba(168, 85, 247, 0.4)' },
  DELETE: { bg: 'rgba(239, 68, 68, 0.15)', text: '#F87171', border: 'rgba(239, 68, 68, 0.4)' },
};

function ApiOnboardingContent({ setActivePage, initialTargetId, initialTab }) {
  const { refreshScans, selectScan, selectTarget: setContextTarget, selectedTargetId } = useScanContext();

  // Navigation state within Onboarding
  const [activeTab, setActiveTab] = useState(initialTab || 'catalog'); // 'catalog' | 'add' | 'discovery' | 'auth' | 'scan'
  
  // Target catalog state
  const [targets, setTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [loadingTargets, setLoadingTargets] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [cardValidation, setCardValidation] = useState({});

  // New Target Form state
  const [formMode, setFormMode] = useState('openapi'); // 'openapi' | 'manual' | 'demo'
  const [newTargetName, setNewTargetName] = useState('');
  const [newTargetUrl, setNewTargetUrl] = useState('');
  const [newTargetEnv, setNewTargetEnv] = useState('development');
  const [newTargetDesc, setNewTargetDesc] = useState('');
  const [specInputMode, setSpecInputMode] = useState('paste'); // 'paste' | 'upload' | 'url'
  const [specContent, setSpecContent] = useState('');
  const [specRemoteUrl, setSpecRemoteUrl] = useState('');
  const [specPreview, setSpecPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submittingTarget, setSubmittingTarget] = useState(false);

  // Endpoints discovery state
  const [endpoints, setEndpoints] = useState([]);
  const [loadingEndpoints, setLoadingEndpoints] = useState(false);
  const [methodFilter, setMethodFilter] = useState('ALL');
  const [sensitiveOnly, setSensitiveOnly] = useState(false);
  const [selectedOnly, setSelectedOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [inspectedEndpoint, setInspectedEndpoint] = useState(null);

  // Auth Profiles state
  const [authProfiles, setAuthProfiles] = useState([]);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  
  // User A form
  const [userAAuthType, setUserAAuthType] = useState('bearer');
  const [userAToken, setUserAToken] = useState('');
  const [userAUsername, setUserAUsername] = useState('alice');
  const [userAHeader, setUserAHeader] = useState('Authorization');
  const [userAResourceId, setUserAResourceId] = useState('101');
  const [savingUserA, setSavingUserA] = useState(false);

  // User B form
  const [userBAuthType, setUserBAuthType] = useState('bearer');
  const [userBToken, setUserBToken] = useState('');
  const [userBUsername, setUserBUsername] = useState('bob');
  const [userBHeader, setUserBHeader] = useState('Authorization');
  const [savingUserB, setSavingUserB] = useState(false);

  // Target Validation state
  const [validatingTarget, setValidatingTarget] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  // Scan Launchpad state
  const [scanProfileName, setScanProfileName] = useState('Targeted Endpoint Security Audit');
  const [scanCategories, setScanCategories] = useState(['BOLA', 'AUTH', 'HEADERS', 'CONFIG']);
  const [userAuthorized, setUserAuthorized] = useState(true);
  const [isLaunchingScan, setIsLaunchingScan] = useState(false);
  const [scanTerminalLogs, setScanTerminalLogs] = useState([]);
  const [scanLaunchResult, setScanLaunchResult] = useState(null);

  // Load targets on mount
  useEffect(() => {
    loadTargets();
  }, []);

  // Sync initial tab and target id when passed
  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  useEffect(() => {
    const targetToSelect = initialTargetId || selectedTargetId;
    if (targetToSelect && targets.length > 0) {
      const match = targets.find(t => t.id === targetToSelect);
      if (match) {
        setSelectedTarget(match);
      }
    }
  }, [initialTargetId, selectedTargetId, targets]);

  // When selected target changes, refresh endpoints and auth profiles
  useEffect(() => {
    if (selectedTarget?.id) {
      loadEndpoints(selectedTarget.id);
      loadAuthProfiles(selectedTarget.id);
      setValidationResult(null);
    }
  }, [selectedTarget?.id]);

  const handleValidateCardTarget = async (e, targetId) => {
    e.stopPropagation();
    setCardValidation(prev => ({ ...prev, [targetId]: { loading: true } }));
    try {
      const res = await apiClient.validateTargetConnectivity(targetId);
      setCardValidation(prev => ({ ...prev, [targetId]: { loading: false, result: res } }));
      if (res.is_valid) {
        showSuccess(`Target connection verified! (${res.latency_ms}ms)`);
      } else {
        showError(`Validation warning: ${res.error_message || 'Target returned non-success'}`);
      }
    } catch (err) {
      setCardValidation(prev => ({ ...prev, [targetId]: { loading: false, error: err.message } }));
      showError(`Validation failed: ${err.message}`);
    }
  };

  const showSuccess = (msg) => {
    setActionSuccess(msg);
    setTimeout(() => setActionSuccess(null), 4000);
  };

  const showError = (msg) => {
    setActionError(msg);
    setTimeout(() => setActionError(null), 6000);
  };

  const loadTargets = async () => {
    setLoadingTargets(true);
    try {
      const data = await apiClient.getTargets({ limit: 50 });
      setTargets(data.items || []);
      if (!selectedTarget && data.items?.length > 0) {
        setSelectedTarget(data.items[0]);
      } else if (selectedTarget) {
        const refreshed = data.items.find(t => t.id === selectedTarget.id);
        if (refreshed) setSelectedTarget(refreshed);
      }
    } catch (err) {
      showError(`Failed to load API targets: ${err.message}`);
    } finally {
      setLoadingTargets(false);
    }
  };

  const loadEndpoints = async (targetId) => {
    setLoadingEndpoints(true);
    try {
      const data = await apiClient.getTargetEndpoints(targetId, {
        method: methodFilter,
        sensitive_only: sensitiveOnly ? true : null,
        selected_only: selectedOnly ? true : null,
        search: searchQuery.trim() || null,
        limit: 250,
      });
      setEndpoints(data.items || []);
    } catch (err) {
      showError(`Failed to load discovered endpoints: ${err.message}`);
    } finally {
      setLoadingEndpoints(false);
    }
  };

  const loadAuthProfiles = async (targetId) => {
    setLoadingProfiles(true);
    try {
      const profiles = await apiClient.getAuthProfiles(targetId);
      setAuthProfiles(profiles || []);
      
      const pA = profiles.find(p => p.account_label === 'User A');
      if (pA) {
        setUserAAuthType(pA.auth_type || 'bearer');
        setUserAUsername(pA.username || 'alice');
        setUserAHeader(pA.header_name || 'Authorization');
        if (pA.owned_resource_id) setUserAResourceId(pA.owned_resource_id);
      }
      const pB = profiles.find(p => p.account_label === 'User B');
      if (pB) {
        setUserBAuthType(pB.auth_type || 'bearer');
        setUserBUsername(pB.username || 'bob');
        setUserBHeader(pB.header_name || 'Authorization');
      }
    } catch (err) {
      // Quiet fail if none exist
      setAuthProfiles([]);
    } finally {
      setLoadingProfiles(false);
    }
  };

  // Live Spec Preview
  const handlePreviewSpec = async () => {
    if (!specContent.trim()) {
      showError('Please paste OpenAPI specification content first.');
      return;
    }
    setPreviewLoading(true);
    setActionError(null);
    try {
      const preview = await apiClient.previewOpenApiSpec(specContent);
      setSpecPreview(preview);
      if (!newTargetName && preview.title) {
        setNewTargetName(preview.title);
      }
      if (!newTargetUrl && preview.base_url) {
        setNewTargetUrl(preview.base_url);
      }
      if (preview.description && !newTargetDesc) {
        setNewTargetDesc(preview.description.substring(0, 200));
      }
      showSuccess(`Spec validated! Detected ${preview.total_endpoints} operations across ${preview.version}.`);
    } catch (err) {
      showError(`OpenAPI validation error: ${err.message}`);
      setSpecPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Spec File Upload Handler
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      showError('Specification file exceeds maximum allowed size of 5 MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === 'string') {
        setSpecContent(content);
        showSuccess(`Loaded ${file.name} (${Math.round(file.size / 1024)} KB)`);
      }
    };
    reader.readAsText(file);
  };

  // Fast 1-Click Load Healthcare Demo API
  const handleLoadDemoApi = async () => {
    setSubmittingTarget(true);
    setActionError(null);
    try {
      // 1. Create target
      const target = await apiClient.createTarget({
        name: 'Healthcare Patient Portal Demo API',
        base_url: DEMO_API_URL,
        environment: 'development',
        description: 'Simulated clinic management API vulnerable to BOLA and missing security headers.',
        api_type: 'REST',
        api_version: '1.0.0',
      });

      // 2. Import demo spec from local URL
      await apiClient.importOpenApiSpec(target.id, {
        spec_url: DEMO_SPEC_URL,
      });

      // 3. Configure dual test accounts
      await apiClient.saveAuthProfile(target.id, {
        account_label: 'User A',
        auth_type: 'bearer',
        token_or_secret: 'alice_demo_token_secret',
        header_name: 'Authorization',
        username: 'alice',
        role: 'patient',
        owned_resource_id: '101',
      });

      await apiClient.saveAuthProfile(target.id, {
        account_label: 'User B',
        auth_type: 'bearer',
        token_or_secret: 'bob_attacker_probe_token',
        header_name: 'Authorization',
        username: 'bob',
        role: 'probe',
      });

      await loadTargets();
      setSelectedTarget(target);
      setActiveTab('discovery');
      showSuccess('Healthcare Demo API registered and 100% configured with dual test accounts!');
    } catch (err) {
      showError(`Demo setup error: ${err.message}`);
    } finally {
      setSubmittingTarget(false);
    }
  };

  // Submit New Target Registration
  const handleCreateTarget = async () => {
    if (!newTargetName.trim()) {
      showError('Target API name is required.');
      return;
    }
    if (!newTargetUrl.trim()) {
      showError('Target Base URL is required.');
      return;
    }
    if (!newTargetUrl.startsWith('http://') && !newTargetUrl.startsWith('https://')) {
      showError('Base URL must begin with http:// or https://');
      return;
    }

    setSubmittingTarget(true);
    setActionError(null);
    try {
      const target = await apiClient.createTarget({
        name: newTargetName.trim(),
        base_url: newTargetUrl.trim(),
        environment: newTargetEnv,
        description: newTargetDesc.trim() || null,
        api_type: 'REST',
      });

      // If spec content or URL provided, import it
      if (formMode === 'openapi') {
        if (specInputMode === 'paste' || specInputMode === 'upload') {
          if (specContent.trim()) {
            await apiClient.importOpenApiSpec(target.id, { spec_content: specContent.trim() });
          }
        } else if (specInputMode === 'url' && specRemoteUrl.trim()) {
          await apiClient.importOpenApiSpec(target.id, { spec_url: specRemoteUrl.trim() });
        }
      }

      await loadTargets();
      setSelectedTarget(target);
      setActiveTab('discovery');
      showSuccess(`Target API "${target.name}" registered successfully!`);
      // Reset form
      setNewTargetName('');
      setNewTargetUrl('');
      setNewTargetDesc('');
      setSpecContent('');
      setSpecRemoteUrl('');
      setSpecPreview(null);
    } catch (err) {
      showError(`Target creation failed: ${err.message}`);
    } finally {
      setSubmittingTarget(false);
    }
  };

  // Delete Target
  const handleDeleteTarget = async (targetId, targetName) => {
    if (!window.confirm(`Are you sure you want to delete target "${targetName}"? Discovered endpoints and authentication profiles will be removed, but historical scan logs will be preserved.`)) {
      return;
    }
    try {
      await apiClient.deleteTarget(targetId);
      showSuccess(`Target "${targetName}" deleted.`);
      if (selectedTarget?.id === targetId) {
        setSelectedTarget(null);
      }
      await loadTargets();
    } catch (err) {
      showError(`Failed to delete target: ${err.message}`);
    }
  };

  // Endpoint Selection Toggle
  const handleToggleEndpoint = async (endpointId, currentSelected) => {
    if (!selectedTarget?.id) return;
    try {
      await apiClient.updateEndpointSelection(selectedTarget.id, {
        endpoint_ids: [{ endpoint_id: endpointId, is_selected: !currentSelected }],
      });
      // Update local state smoothly
      setEndpoints(prev => prev.map(ep => ep.id === endpointId ? { ...ep, is_selected: !currentSelected } : ep));
      // Update selected target count in state
      setSelectedTarget(prev => prev ? {
        ...prev,
        selected_endpoint_count: Math.max(0, (prev.selected_endpoint_count || 0) + (currentSelected ? -1 : 1))
      } : prev);
    } catch (err) {
      showError(`Failed to update endpoint selection: ${err.message}`);
    }
  };

  // Bulk Selection Handlers
  const handleBulkSelect = async (action) => {
    if (!selectedTarget?.id) return;
    try {
      let payload = {};
      if (action === 'all') payload = { select_all: true };
      else if (action === 'none') payload = { deselect_all: true };
      else if (action === 'sensitive') payload = { sensitive_only: true };

      const res = await apiClient.updateEndpointSelection(selectedTarget.id, payload);
      showSuccess(`Endpoint selection updated (${res.selected_count} endpoints selected)`);
      loadEndpoints(selectedTarget.id);
      loadTargets();
    } catch (err) {
      showError(`Bulk selection error: ${err.message}`);
    }
  };

  // Save Auth Profile
  const handleSaveAuthProfile = async (label) => {
    if (!selectedTarget?.id) return;
    const isA = label === 'User A';
    const authType = isA ? userAAuthType : userBAuthType;
    const token = isA ? userAToken : userBToken;
    const username = isA ? userAUsername : userBUsername;
    const header = isA ? userAHeader : userBHeader;
    const resourceId = isA ? userAResourceId : null;

    if (isA) setSavingUserA(true);
    else setSavingUserB(true);

    try {
      const payload = {
        account_label: label,
        auth_type: authType,
        token_or_secret: token.trim() || undefined,
        header_name: header.trim() || 'Authorization',
        username: username.trim() || undefined,
        role: isA ? 'owner' : 'probe',
      };
      if (isA && resourceId) payload.owned_resource_id = resourceId.trim();

      await apiClient.saveAuthProfile(selectedTarget.id, payload);
      showSuccess(`${label} authentication profile encrypted and saved.`);
      if (isA) setUserAToken('');
      else setUserBToken('');
      loadAuthProfiles(selectedTarget.id);
    } catch (err) {
      showError(`Failed to save ${label}: ${err.message}`);
    } finally {
      if (isA) setSavingUserA(false);
      else setSavingUserB(false);
    }
  };

  // Target Connectivity Validation
  const handleValidateTarget = async () => {
    if (!selectedTarget?.id) return;
    setValidatingTarget(true);
    setValidationResult(null);
    try {
      const res = await apiClient.validateTargetConnectivity(selectedTarget.id);
      setValidationResult(res);
      if (res.is_valid) {
        showSuccess(`Target validation successful! HTTP ${res.status_code || 200} (${res.latency_ms}ms)`);
      } else {
        showError(`Validation warning: ${res.error_message || 'Target returned an error status'}`);
      }
    } catch (err) {
      showError(`Validation failed: ${err.message}`);
    } finally {
      setValidatingTarget(false);
    }
  };

  // Launch Targeted Scan Bridge
  const handleLaunchScan = async () => {
    if (!selectedTarget?.id) return;
    if (!userAuthorized) {
      showError('You must confirm security testing authorization.');
      return;
    }

    setIsLaunchingScan(true);
    setScanLaunchResult(null);
    setScanTerminalLogs([
      `[INIT] Launching Targeted Security Audit against "${selectedTarget.name}" (${selectedTarget.base_url})...`,
      `[DISCOVERY] Loading ${(selectedTarget.selected_endpoint_count || 0)} selected target operations...`,
      `[VAULT] Decrypting Fernet-encrypted test credentials for User A and User B...`,
      `[ENGINE] Mapping dual principals to Member 1 BOLA/IDOR detection matrix...`,
      `[SOCKET] Enforcing destination IP pinning and SSRF defense on all HTTP transport...`,
    ]);

    try {
      const result = await apiClient.launchTargetScan(selectedTarget.id, {
        scan_profile: scanProfileName,
        categories: scanCategories,
        user_authorized: true,
      });

      setScanTerminalLogs(prev => [
        ...prev,
        `[EXEC] Member 1 Detection Engine executed tests: [${scanCategories.join(', ')}]`,
        `[PROBING] Evaluated sensitive IDOR endpoints with cross-principal tokens.`,
        `[COMPLETE] Scan ${result.id.substring(0, 8)} finished with status: ${result.status}`,
        `[FINDINGS] Total vulnerabilities detected: ${result.total_findings}`,
        `[PERSIST] Target last scan timestamp updated: ${new Date().toLocaleTimeString()}`,
      ]);

      setScanLaunchResult(result);
      await refreshScans(result.id);
      await loadTargets();
      showSuccess(`Security scan completed with ${result.total_findings} findings!`);
    } catch (err) {
      setScanTerminalLogs(prev => [
        ...prev,
        `[ERROR] Scan execution failed: ${err.message}`,
      ]);
      showError(`Scan execution error: ${err.message}`);
    } finally {
      setIsLaunchingScan(false);
    }
  };

  // Filtered Endpoints List
  const displayedEndpoints = useMemo(() => {
    return endpoints.filter(ep => {
      if (methodFilter !== 'ALL' && ep.method !== methodFilter) return false;
      if (sensitiveOnly && !ep.is_sensitive_candidate) return false;
      if (selectedOnly && !ep.is_selected) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const pMatch = ep.path.toLowerCase().includes(q);
        const sMatch = ep.summary && ep.summary.toLowerCase().includes(q);
        const oMatch = ep.operation_id && ep.operation_id.toLowerCase().includes(q);
        if (!pMatch && !sMatch && !oMatch) return false;
      }
      return true;
    });
  }, [endpoints, methodFilter, sensitiveOnly, selectedOnly, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Top Banner Alert Bar */}
      {actionSuccess && (
        <div style={{
          backgroundColor: 'rgba(34, 197, 94, 0.12)',
          border: '1px solid rgba(34, 197, 94, 0.35)',
          borderRadius: '8px',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#4ADE80',
          fontSize: '0.88rem'
        }}>
          <CheckCircle2 size={18} />
          <span>{actionSuccess}</span>
        </div>
      )}
      {actionError && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '8px',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#F87171',
          fontSize: '0.88rem'
        }}>
          <AlertCircle size={18} />
          <span>{actionError}</span>
        </div>
      )}

      {/* Main Tab Navigation Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: '#07182B',
        border: '1px solid rgba(0, 200, 255, 0.15)',
        borderRadius: '12px',
        padding: '8px 12px',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {[
            { id: 'catalog', label: '1. Target APIs', icon: Server, count: targets.length },
            { id: 'add', label: '2. Register API / Spec', icon: PlusCircle },
            { id: 'discovery', label: '3. Endpoints & Discovery', icon: Layers, count: endpoints.length, disabled: !selectedTarget },
            { id: 'auth', label: '4. Authentication (BOLA)', icon: Key, count: authProfiles.length, disabled: !selectedTarget },
            { id: 'scan', label: '5. Launch Targeted Scan', icon: Play, disabled: !selectedTarget },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const isDisabled = tab.disabled;
            return (
              <button
                key={tab.id}
                onClick={() => !isDisabled && setActiveTab(tab.id)}
                disabled={isDisabled}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 16px',
                  borderRadius: '8px',
                  border: isActive ? '1px solid #19D3FF' : '1px solid transparent',
                  backgroundColor: isActive ? 'rgba(25, 211, 255, 0.12)' : 'transparent',
                  color: isDisabled ? '#4B6382' : isActive ? '#19D3FF' : '#94A3B8',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 600 : 500,
                  cursor: isDisabled ? 'not-allowed' : 'pointer',
                  transition: 'all 0.18s ease',
                  opacity: isDisabled ? 0.5 : 1,
                }}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span style={{
                    backgroundColor: isActive ? '#19D3FF' : 'rgba(255, 255, 255, 0.08)',
                    color: isActive ? '#050D1F' : '#94A3B8',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    fontSize: '0.72rem',
                    fontWeight: 700
                  }}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Selected Target Quick Indicator */}
        {selectedTarget && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            backgroundColor: 'rgba(13, 34, 58, 0.8)',
            padding: '6px 14px',
            borderRadius: '8px',
            border: '1px solid rgba(0, 200, 255, 0.2)'
          }}>
            <span style={{ fontSize: '0.75rem', color: '#6482A6' }}>Active Target:</span>
            <span style={{ fontSize: '0.84rem', fontWeight: 600, color: '#F1F5F9' }}>{selectedTarget.name}</span>
            <span style={{
              fontSize: '0.7rem',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(25, 211, 255, 0.15)',
              color: '#19D3FF',
              fontFamily: 'monospace'
            }}>
              {selectedTarget.environment}
            </span>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: TARGET CATALOG & OVERVIEW                                          */}
      {/* ========================================================================= */}
      {activeTab === 'catalog' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Header Action Card */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '12px',
            border: '1px solid rgba(0, 200, 255, 0.15)',
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 6px 0' }}>
                Configured API Targets ({targets.length})
              </h2>
              <p style={{ fontSize: '0.85rem', color: '#8AA4C8', margin: 0 }}>
                Manage target APIs, imported OpenAPI/Swagger specifications, and isolated test configurations.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={loadTargets}
                disabled={loadingTargets}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#CBD5E1',
                  borderRadius: '8px',
                  padding: '9px 16px',
                  fontSize: '0.85rem',
                  cursor: 'pointer'
                }}
              >
                <RefreshCw size={15} className={loadingTargets ? 'animate-spin' : ''} />
                Refresh
              </button>
              <button
                onClick={() => setActiveTab('add')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#19D3FF',
                  border: 'none',
                  color: '#050D1F',
                  borderRadius: '8px',
                  padding: '9px 18px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <PlusCircle size={16} />
                + Register New API
              </button>
            </div>
          </div>

          {/* Targets Grid */}
          {targets.length === 0 ? (
            <div style={{
              backgroundColor: '#07182B',
              borderRadius: '12px',
              border: '1px dashed rgba(0, 200, 255, 0.25)',
              padding: '48px 24px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '16px'
            }}>
              <Server size={44} color="#6482A6" />
              <div>
                <h3 style={{ fontSize: '1.1rem', color: '#F1F5F9', margin: '0 0 8px 0' }}>No API Targets Configured</h3>
                <p style={{ fontSize: '0.85rem', color: '#8AA4C8', maxWidth: '480px', margin: '0 auto' }}>
                  Register your own REST API endpoint or load the pre-configured local Healthcare Demo API to begin endpoint discovery and security testing.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                <button
                  onClick={handleLoadDemoApi}
                  disabled={submittingTarget}
                  style={{
                    backgroundColor: 'rgba(25, 211, 255, 0.15)',
                    border: '1px solid #19D3FF',
                    color: '#19D3FF',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <SparklesIcon size={16} />
                  1-Click Load Healthcare Demo API
                </button>
                <button
                  onClick={() => setActiveTab('add')}
                  style={{
                    backgroundColor: '#19D3FF',
                    border: 'none',
                    color: '#050D1F',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Register Custom API
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 380px), 1fr))', gap: '16px', width: '100%', boxSizing: 'border-box' }}>
              {targets.map(target => {
                const isSelected = selectedTarget?.id === target.id;
                return (
                  <div
                    key={target.id}
                    onClick={() => setSelectedTarget(target)}
                    style={{
                      backgroundColor: '#07182B',
                      borderRadius: '12px',
                      border: isSelected ? '1px solid #19D3FF' : '1px solid rgba(0, 200, 255, 0.15)',
                      boxShadow: isSelected ? '0 0 16px rgba(25, 211, 255, 0.15)' : 'none',
                      padding: '18px 20px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '14px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxSizing: 'border-box',
                      minWidth: 0,
                      overflow: 'hidden',
                      position: 'relative'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '8px' }}>
                        <div>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 4px 0' }}>
                            {target.name}
                          </h3>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{
                              fontFamily: 'monospace',
                              fontSize: '0.78rem',
                              color: '#60A5FA',
                              wordBreak: 'break-all'
                            }}>
                              {target.base_url}
                            </span>
                          </div>
                        </div>
                        <span style={{
                          fontSize: '0.72rem',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          backgroundColor: 'rgba(25, 211, 255, 0.12)',
                          color: '#19D3FF',
                          fontWeight: 600,
                          textTransform: 'uppercase'
                        }}>
                          {target.environment}
                        </span>
                      </div>

                      {target.description && (
                        <p style={{ fontSize: '0.8rem', color: '#8AA4C8', margin: '0 0 14px 0', lineHeight: 1.4 }}>
                          {target.description}
                        </p>
                      )}

                      {/* Endpoint & Spec Metrics */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '8px',
                        backgroundColor: 'rgba(13, 34, 58, 0.6)',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        border: '1px solid rgba(0, 200, 255, 0.1)'
                      }}>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: '#6482A6' }}>Discovered</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#F1F5F9' }}>
                            {target.endpoint_count || 0}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: '#6482A6' }}>Selected</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38BDF8' }}>
                            {target.selected_endpoint_count || 0}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: '#6482A6' }}>Sensitive IDOR</div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#FBBF24' }}>
                            {target.sensitive_endpoint_count || 0}
                          </div>
                        </div>
                      </div>

                      {/* Last scan timestamp */}
                      <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#6482A6', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Spec: {target.specification_version || 'None'}</span>
                        <span>Last scan: {target.last_scan_at ? new Date(target.last_scan_at).toLocaleDateString() : 'Never'}</span>
                      </div>

                      {/* Real-time Connectivity Badge */}
                      {cardValidation[target.id] && (
                        <div style={{
                          marginTop: '8px',
                          padding: '6px 10px',
                          borderRadius: '6px',
                          fontSize: '0.74rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          backgroundColor: cardValidation[target.id].result?.is_valid ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                          border: `1px solid ${cardValidation[target.id].result?.is_valid ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                          color: cardValidation[target.id].result?.is_valid ? '#4ADE80' : '#F87171'
                        }}>
                          <span>{cardValidation[target.id].result?.is_valid ? '✓ Reachable & Safe' : (cardValidation[target.id].error || 'Connectivity Warning')}</span>
                          <span>{cardValidation[target.id].result?.latency_ms ? `${cardValidation[target.id].result.latency_ms}ms` : ''}</span>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr) auto',
                      alignItems: 'center',
                      gap: '5px',
                      paddingTop: '12px',
                      borderTop: '1px solid rgba(0, 200, 255, 0.1)',
                      width: '100%',
                      boxSizing: 'border-box'
                    }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTarget(target);
                          setActiveTab('discovery');
                        }}
                        title="View Endpoints"
                        style={{
                          width: '100%',
                          minWidth: 0,
                          backgroundColor: 'rgba(25, 211, 255, 0.1)',
                          border: '1px solid rgba(25, 211, 255, 0.3)',
                          color: '#19D3FF',
                          borderRadius: '6px',
                          padding: '7px 4px',
                          fontSize: '0.74rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '3px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          boxSizing: 'border-box'
                        }}
                      >
                        <Layers size={12} style={{ flexShrink: 0 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>Endpoints</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTarget(target);
                          setActiveTab('auth');
                        }}
                        title="Authentication Settings"
                        style={{
                          width: '100%',
                          minWidth: 0,
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.15)',
                          color: '#E2E8F0',
                          borderRadius: '6px',
                          padding: '7px 4px',
                          fontSize: '0.74rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '3px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          boxSizing: 'border-box'
                        }}
                      >
                        <Key size={12} style={{ flexShrink: 0 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>Auth</span>
                      </button>
                      <button
                        onClick={(e) => handleValidateCardTarget(e, target.id)}
                        disabled={cardValidation[target.id]?.loading}
                        title="Validate Target Connectivity"
                        style={{
                          width: '100%',
                          minWidth: 0,
                          backgroundColor: 'rgba(34, 197, 94, 0.1)',
                          border: '1px solid rgba(34, 197, 94, 0.3)',
                          color: '#4ADE80',
                          borderRadius: '6px',
                          padding: '7px 4px',
                          fontSize: '0.74rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '3px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          boxSizing: 'border-box'
                        }}
                      >
                        <CheckCircle2 size={12} className={cardValidation[target.id]?.loading ? 'animate-spin' : ''} style={{ flexShrink: 0 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{cardValidation[target.id]?.loading ? '...' : 'Validate'}</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTarget(target);
                          if (setContextTarget) setContextTarget(target.id);
                          setActivePage('scans', { targetId: target.id, tab: 'new' });
                        }}
                        title="Launch Targeted Scan"
                        style={{
                          width: '100%',
                          minWidth: 0,
                          backgroundColor: '#19D3FF',
                          border: 'none',
                          color: '#050D1F',
                          borderRadius: '6px',
                          padding: '7px 4px',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '3px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          boxSizing: 'border-box'
                        }}
                      >
                        <Play size={12} style={{ flexShrink: 0 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>Scan</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteTarget(target.id, target.name);
                        }}
                        title="Delete Target"
                        style={{
                          flexShrink: 0,
                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          color: '#F87171',
                          borderRadius: '6px',
                          padding: '7px 8px',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxSizing: 'border-box'
                        }}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: REGISTER API / OPENAPI IMPORT                                      */}
      {/* ========================================================================= */}
      {activeTab === 'add' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '880px', margin: '0 auto', width: '100%' }}>
          
          {/* Method Selector */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '12px'
          }}>
            {[
              { id: 'openapi', label: 'Import OpenAPI / Swagger', desc: 'JSON or YAML specification with live preview', icon: FileCode },
              { id: 'demo', label: 'Healthcare Demo API', desc: '1-click setup with pre-seeded vulnerable BOLA endpoints', icon: SparklesIcon },
              { id: 'manual', label: 'Manual Base Registration', desc: 'Quick URL registration for manual auditing', icon: Globe },
            ].map(m => {
              const Icon = m.icon;
              const isSelected = formMode === m.id;
              return (
                <div
                  key={m.id}
                  onClick={() => setFormMode(m.id)}
                  style={{
                    backgroundColor: '#07182B',
                    borderRadius: '10px',
                    border: isSelected ? '1px solid #19D3FF' : '1px solid rgba(0, 200, 255, 0.15)',
                    padding: '16px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? '0 0 12px rgba(25, 211, 255, 0.12)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <Icon size={18} color={isSelected ? '#19D3FF' : '#94A3B8'} />
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: isSelected ? '#19D3FF' : '#F1F5F9' }}>
                      {m.label}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#8AA4C8', margin: 0, lineHeight: 1.35 }}>
                    {m.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* 1-Click Demo API Box */}
          {formMode === 'demo' && (
            <div style={{
              backgroundColor: '#07182B',
              borderRadius: '12px',
              border: '1px solid rgba(25, 211, 255, 0.3)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#F1F5F9', margin: '0 0 6px 0' }}>
                  Load Pre-configured Healthcare Demo Target
                </h3>
                <p style={{ fontSize: '0.85rem', color: '#8AA4C8', margin: 0, lineHeight: 1.4 }}>
                  API Sentinel includes a fully functioning local lab API running on port 8001. 
                  Clicking below will automatically register it, import its OpenAPI spec, and configure two test accounts (Alice and Bob) for dual-principal BOLA/IDOR auditing.
                </p>
              </div>

              <div style={{
                backgroundColor: 'rgba(13, 34, 58, 0.8)',
                padding: '14px 18px',
                borderRadius: '8px',
                border: '1px solid rgba(0, 200, 255, 0.15)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                fontSize: '0.82rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6482A6' }}>Target Base URL:</span>
                  <span style={{ fontFamily: 'monospace', color: '#60A5FA' }}>http://127.0.0.1:8001</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6482A6' }}>OpenAPI Spec URL:</span>
                  <span style={{ fontFamily: 'monospace', color: '#60A5FA' }}>http://127.0.0.1:8001/openapi.json</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6482A6' }}>Pre-configured Principals:</span>
                  <span style={{ color: '#4ADE80' }}>User A (Alice - Patient 101) & User B (Bob - Probe)</span>
                </div>
              </div>

              <button
                onClick={handleLoadDemoApi}
                disabled={submittingTarget}
                style={{
                  backgroundColor: '#19D3FF',
                  border: 'none',
                  color: '#050D1F',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  cursor: submittingTarget ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '10px'
                }}
              >
                {submittingTarget ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Registering Demo API & Importing Spec...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Instantly Load Healthcare Demo API
                  </>
                )}
              </button>
            </div>
          )}

          {/* Form for OpenAPI or Manual */}
          {formMode !== 'demo' && (
            <div style={{
              backgroundColor: '#07182B',
              borderRadius: '12px',
              border: '1px solid rgba(0, 200, 255, 0.15)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px'
            }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#F1F5F9', margin: 0 }}>
                {formMode === 'openapi' ? 'Import OpenAPI Specification' : 'Manual Target Configuration'}
              </h3>

              {/* Target Basic Fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#8AA4C8', marginBottom: '6px' }}>
                    API Name *
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Orders & Billing Microservice"
                    value={newTargetName}
                    onChange={(e) => setNewTargetName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: 'rgba(13, 34, 58, 0.6)',
                      border: '1px solid rgba(0, 200, 255, 0.25)',
                      borderRadius: '8px',
                      color: '#F1F5F9',
                      fontSize: '0.85rem',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#8AA4C8', marginBottom: '6px' }}>
                    Environment
                  </label>
                  <select
                    value={newTargetEnv}
                    onChange={(e) => setNewTargetEnv(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#0D223A',
                      border: '1px solid rgba(0, 200, 255, 0.25)',
                      borderRadius: '8px',
                      color: '#F1F5F9',
                      fontSize: '0.85rem',
                      boxSizing: 'border-box'
                    }}
                  >
                    <option value="development">Development (Local / Lab)</option>
                    <option value="staging">Staging / QA</option>
                    <option value="production">Production</option>
                    <option value="testing">Automated Testing</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#8AA4C8', marginBottom: '6px' }}>
                  Target Base URL *
                </label>
                <input
                  type="text"
                  placeholder="https://api.yourcompany.com or http://127.0.0.1:8001"
                  value={newTargetUrl}
                  onChange={(e) => setNewTargetUrl(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.25)',
                    borderRadius: '8px',
                    color: '#F1F5F9',
                    fontSize: '0.85rem',
                    boxSizing: 'border-box',
                    fontFamily: 'monospace'
                  }}
                />
              </div>

              {/* OpenAPI Specific Input */}
              {formMode === 'openapi' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <label style={{ fontSize: '0.8rem', color: '#8AA4C8' }}>
                      Specification Input Method
                    </label>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {[
                        { id: 'paste', label: 'Paste Spec (JSON/YAML)' },
                        { id: 'upload', label: 'Upload File' },
                        { id: 'url', label: 'Remote Spec URL' },
                      ].map(im => (
                        <button
                          key={im.id}
                          onClick={() => setSpecInputMode(im.id)}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '6px',
                            border: specInputMode === im.id ? '1px solid #19D3FF' : '1px solid rgba(255,255,255,0.1)',
                            backgroundColor: specInputMode === im.id ? 'rgba(25, 211, 255, 0.15)' : 'transparent',
                            color: specInputMode === im.id ? '#19D3FF' : '#94A3B8',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          {im.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {specInputMode === 'paste' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <textarea
                        rows={8}
                        placeholder="Paste your OpenAPI 3.0 / 3.1 or Swagger 2.0 JSON/YAML specification here..."
                        value={specContent}
                        onChange={(e) => setSpecContent(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '12px',
                          backgroundColor: '#050D1F',
                          border: '1px solid rgba(0, 200, 255, 0.2)',
                          borderRadius: '8px',
                          color: '#E2E8F0',
                          fontFamily: 'monospace',
                          fontSize: '0.8rem',
                          boxSizing: 'border-box',
                          resize: 'vertical'
                        }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                          onClick={handlePreviewSpec}
                          disabled={previewLoading || !specContent.trim()}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            backgroundColor: 'rgba(25, 211, 255, 0.1)',
                            border: '1px solid rgba(25, 211, 255, 0.3)',
                            color: '#19D3FF',
                            borderRadius: '6px',
                            padding: '6px 14px',
                            fontSize: '0.78rem',
                            cursor: 'pointer'
                          }}
                        >
                          <Eye size={14} />
                          {previewLoading ? 'Parsing...' : 'Live Spec Preview'}
                        </button>
                      </div>
                    </div>
                  )}

                  {specInputMode === 'upload' && (
                    <div style={{
                      border: '2px dashed rgba(0, 200, 255, 0.25)',
                      borderRadius: '8px',
                      padding: '28px 18px',
                      textAlign: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '10px'
                    }}>
                      <Upload size={28} color="#19D3FF" />
                      <div style={{ fontSize: '0.85rem', color: '#F1F5F9' }}>
                        Choose OpenAPI JSON (.json) or YAML (.yaml, .yml) file
                      </div>
                      <input
                        type="file"
                        accept=".json,.yaml,.yml"
                        onChange={handleFileUpload}
                        style={{ fontSize: '0.8rem', color: '#8AA4C8' }}
                      />
                      {specContent && (
                        <div style={{ color: '#4ADE80', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Check size={14} /> Spec file loaded ({Math.round(specContent.length / 1024)} KB)
                        </div>
                      )}
                    </div>
                  )}

                  {specInputMode === 'url' && (
                    <div>
                      <input
                        type="text"
                        placeholder="e.g. http://127.0.0.1:8001/openapi.json or https://api.service.com/v3/api-docs"
                        value={specRemoteUrl}
                        onChange={(e) => setSpecRemoteUrl(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '10px 14px',
                          backgroundColor: 'rgba(13, 34, 58, 0.6)',
                          border: '1px solid rgba(0, 200, 255, 0.25)',
                          borderRadius: '8px',
                          color: '#F1F5F9',
                          fontSize: '0.85rem',
                          boxSizing: 'border-box',
                          fontFamily: 'monospace'
                        }}
                      />
                      <span style={{ fontSize: '0.72rem', color: '#6482A6', marginTop: '4px', display: 'block' }}>
                        SSRF protection active: Remote specifications cannot target cloud metadata services (169.254.169.254) or unspecified loopbacks.
                      </span>
                    </div>
                  )}

                  {/* Spec Preview Card */}
                  {specPreview && (
                    <div style={{
                      backgroundColor: 'rgba(13, 34, 58, 0.9)',
                      border: '1px solid rgba(25, 211, 255, 0.3)',
                      borderRadius: '8px',
                      padding: '14px 18px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#19D3FF' }}>
                          Spec Preview: {specPreview.title || 'Untitled API'}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                          Format: {specPreview.version}
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', fontSize: '0.78rem' }}>
                        <div>Total Operations: <strong style={{ color: '#F1F5F9' }}>{specPreview.total_endpoints}</strong></div>
                        <div>Sensitive Candidates: <strong style={{ color: '#FBBF24' }}>{specPreview.sensitive_endpoints}</strong></div>
                        <div>State-Changing: <strong style={{ color: '#F87171' }}>{specPreview.state_changing_operations}</strong></div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  onClick={() => setActiveTab('catalog')}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#94A3B8',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTarget}
                  disabled={submittingTarget}
                  style={{
                    backgroundColor: '#19D3FF',
                    border: 'none',
                    color: '#050D1F',
                    borderRadius: '8px',
                    padding: '10px 22px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: submittingTarget ? 'wait' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  {submittingTarget ? (
                    <>
                      <RefreshCw size={15} className="animate-spin" />
                      Registering Target...
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      Register & Discover Endpoints
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: DISCOVERY & ENDPOINT EXPLORER                                      */}
      {/* ========================================================================= */}
      {activeTab === 'discovery' && selectedTarget && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Header Bar with Quick Stats & Bulk Actions */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '12px',
            border: '1px solid rgba(0, 200, 255, 0.15)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '14px'
          }}>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 4px 0' }}>
                Discovered Endpoints for {selectedTarget.name}
              </h2>
              <p style={{ fontSize: '0.8rem', color: '#8AA4C8', margin: 0 }}>
                Filter, inspect parameters, and select which endpoints to target during security scans.
              </p>
            </div>

            {/* Bulk Selection Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: '#6482A6' }}>Bulk Select:</span>
              <button
                onClick={() => handleBulkSelect('all')}
                style={{
                  backgroundColor: 'rgba(25, 211, 255, 0.12)',
                  border: '1px solid rgba(25, 211, 255, 0.3)',
                  color: '#19D3FF',
                  borderRadius: '6px',
                  padding: '5px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Select All ({endpoints.length})
              </button>
              <button
                onClick={() => handleBulkSelect('sensitive')}
                style={{
                  backgroundColor: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  color: '#FBBF24',
                  borderRadius: '6px',
                  padding: '5px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Select Sensitive IDOR Only
              </button>
              <button
                onClick={() => handleBulkSelect('none')}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#94A3B8',
                  borderRadius: '6px',
                  padding: '5px 10px',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                Deselect All
              </button>
            </div>
          </div>

          {/* Filter and Search Bar */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '10px',
            border: '1px solid rgba(0, 200, 255, 0.12)',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            {/* Method Filter Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {['ALL', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map(m => {
                const isActive = methodFilter === m;
                const mColors = METHOD_COLORS[m] || { bg: 'rgba(255,255,255,0.08)', text: '#F1F5F9' };
                return (
                  <button
                    key={m}
                    onClick={() => setMethodFilter(m)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      border: isActive ? `1px solid ${mColors.text}` : '1px solid transparent',
                      backgroundColor: isActive ? mColors.bg : 'transparent',
                      color: isActive ? mColors.text : '#8AA4C8',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {m}
                  </button>
                );
              })}
            </div>

            {/* Sensitive & Selected Toggles */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#FBBF24', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={sensitiveOnly}
                  onChange={(e) => setSensitiveOnly(e.target.checked)}
                />
                Sensitive IDOR Candidates
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#38BDF8', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={selectedOnly}
                  onChange={(e) => setSelectedOnly(e.target.checked)}
                />
                Selected Only
              </label>
            </div>

            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: '220px' }}>
              <Search size={14} color="#6482A6" style={{ position: 'absolute', left: '10px', top: '10px' }} />
              <input
                type="text"
                placeholder="Search path or operation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '7px 10px 7px 32px',
                  backgroundColor: 'rgba(13, 34, 58, 0.6)',
                  border: '1px solid rgba(0, 200, 255, 0.2)',
                  borderRadius: '6px',
                  color: '#F1F5F9',
                  fontSize: '0.78rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          {/* Endpoints Table */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '12px',
            border: '1px solid rgba(0, 200, 255, 0.15)',
            overflow: 'hidden'
          }}>
            {loadingEndpoints ? (
              <div style={{ padding: '36px', textAlign: 'center', color: '#8AA4C8', fontSize: '0.85rem' }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px auto', display: 'block' }} />
                Loading discovered operations...
              </div>
            ) : displayedEndpoints.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#8AA4C8', fontSize: '0.85rem' }}>
                No endpoints matched your filter criteria.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{
                    backgroundColor: 'rgba(13, 34, 58, 0.9)',
                    borderBottom: '1px solid rgba(0, 200, 255, 0.15)',
                    color: '#8AA4C8',
                    fontSize: '0.75rem',
                    textTransform: 'uppercase'
                  }}>
                    <th style={{ padding: '12px 16px', width: '40px', textAlign: 'center' }}>Target</th>
                    <th style={{ padding: '12px 16px', width: '90px' }}>Method</th>
                    <th style={{ padding: '12px 16px' }}>Path & Summary</th>
                    <th style={{ padding: '12px 16px', width: '180px' }}>Security Markers</th>
                    <th style={{ padding: '12px 16px', width: '130px', textAlign: 'right' }}>Parameters</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedEndpoints.map((ep) => {
                    const mColors = METHOD_COLORS[ep.method] || { bg: 'rgba(255,255,255,0.08)', text: '#94A3B8' };
                    return (
                      <tr
                        key={ep.id}
                        onClick={() => setInspectedEndpoint(ep)}
                        style={{
                          borderBottom: '1px solid rgba(15, 47, 78, 0.5)',
                          cursor: 'pointer',
                          backgroundColor: ep.is_selected ? 'rgba(25, 211, 255, 0.03)' : 'transparent',
                          transition: 'background-color 0.15s ease'
                        }}
                      >
                        {/* Checkbox */}
                        <td
                          style={{ padding: '12px 16px', textAlign: 'center' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleEndpoint(ep.id, ep.is_selected);
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={ep.is_selected}
                            onChange={() => {}}
                            style={{ cursor: 'pointer' }}
                          />
                        </td>

                        {/* Method Badge */}
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: mColors.bg,
                            color: mColors.text,
                            border: `1px solid ${mColors.border || 'transparent'}`,
                            fontWeight: 700,
                            fontSize: '0.72rem'
                          }}>
                            {ep.method}
                          </span>
                        </td>

                        {/* Path & Summary */}
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontFamily: 'monospace', fontWeight: 600, color: '#F1F5F9', marginBottom: '2px' }}>
                            {ep.path}
                          </div>
                          {ep.summary && (
                            <div style={{ fontSize: '0.75rem', color: '#8AA4C8' }}>
                              {ep.summary}
                            </div>
                          )}
                        </td>

                        {/* Security Markers */}
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {ep.is_sensitive_candidate && (
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '2px 7px',
                                borderRadius: '4px',
                                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                                color: '#FBBF24',
                                fontSize: '0.7rem',
                                fontWeight: 600
                              }}>
                                <AlertTriangle size={11} />
                                Sensitive IDOR
                              </span>
                            )}
                            {ep.is_state_changing && (
                              <span style={{
                                padding: '2px 6px',
                                borderRadius: '4px',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                color: '#F87171',
                                fontSize: '0.7rem'
                              }}>
                                Mutating
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Parameters & Schema */}
                        <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                          <span style={{
                            fontSize: '0.72rem',
                            color: '#6482A6',
                            backgroundColor: 'rgba(13, 34, 58, 0.8)',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            border: '1px solid rgba(0, 200, 255, 0.1)'
                          }}>
                            {ep.parameters ? `${ep.parameters.length} params` : '0 params'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Endpoint Inspector Modal / Drawer */}
          {inspectedEndpoint && (
            <div style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: '460px',
              backgroundColor: '#07182B',
              borderLeft: '1px solid rgba(0, 200, 255, 0.25)',
              boxShadow: '-8px 0 24px rgba(0, 0, 0, 0.6)',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              padding: '24px',
              boxSizing: 'border-box',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div>
                  <span style={{
                    display: 'inline-block',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: METHOD_COLORS[inspectedEndpoint.method]?.bg,
                    color: METHOD_COLORS[inspectedEndpoint.method]?.text,
                    fontWeight: 700,
                    fontSize: '0.75rem',
                    marginBottom: '8px'
                  }}>
                    {inspectedEndpoint.method}
                  </span>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#F1F5F9', margin: 0, fontFamily: 'monospace', wordBreak: 'break-all' }}>
                    {inspectedEndpoint.path}
                  </h3>
                </div>
                <button
                  onClick={() => setInspectedEndpoint(null)}
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#8AA4C8',
                    cursor: 'pointer',
                    fontSize: '1.2rem',
                    padding: '4px'
                  }}
                >
                  ✕
                </button>
              </div>

              {inspectedEndpoint.summary && (
                <div style={{ fontSize: '0.82rem', color: '#94A3B8', marginBottom: '16px', lineHeight: 1.4 }}>
                  {inspectedEndpoint.summary}
                </div>
              )}

              {/* Target Toggle in Drawer */}
              <div style={{
                backgroundColor: 'rgba(13, 34, 58, 0.7)',
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px solid rgba(0, 200, 255, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '18px'
              }}>
                <span style={{ fontSize: '0.8rem', color: '#E2E8F0' }}>Include in Security Scans:</span>
                <input
                  type="checkbox"
                  checked={inspectedEndpoint.is_selected}
                  onChange={() => {
                    handleToggleEndpoint(inspectedEndpoint.id, inspectedEndpoint.is_selected);
                    setInspectedEndpoint(prev => ({ ...prev, is_selected: !prev.is_selected }));
                  }}
                  style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                />
              </div>

              {/* Sensitive Candidate Reason */}
              {inspectedEndpoint.is_sensitive_candidate && (
                <div style={{
                  backgroundColor: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  borderRadius: '8px',
                  padding: '12px',
                  fontSize: '0.78rem',
                  color: '#FBBF24',
                  marginBottom: '18px',
                  display: 'flex',
                  gap: '8px'
                }}>
                  <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Flagged for BOLA / IDOR Verification:</strong>
                    <div style={{ marginTop: '4px', color: '#FDE68A' }}>
                      {inspectedEndpoint.sensitivity_reason || 'Endpoint path or parameters contain sensitive identifier tokens (e.g. {id}, patient, user).'}
                    </div>
                  </div>
                </div>
              )}

              {/* Parameters List */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '0.85rem', color: '#8AA4C8', margin: '0 0 10px 0', textTransform: 'uppercase' }}>
                  Parameters ({inspectedEndpoint.parameters?.length || 0})
                </h4>
                {!inspectedEndpoint.parameters || inspectedEndpoint.parameters.length === 0 ? (
                  <div style={{ fontSize: '0.78rem', color: '#6482A6' }}>No declared parameters</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {inspectedEndpoint.parameters.map((p, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: 'rgba(13, 34, 58, 0.6)',
                          borderRadius: '6px',
                          padding: '8px 12px',
                          border: '1px solid rgba(0, 200, 255, 0.1)',
                          fontSize: '0.78rem'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38BDF8' }}>
                            {p.name}
                          </span>
                          <span style={{ fontSize: '0.7rem', color: '#94A3B8' }}>
                            in: <strong>{p.in}</strong> {p.required && <span style={{ color: '#F87171' }}>(required)</span>}
                          </span>
                        </div>
                        {p.description && (
                          <div style={{ fontSize: '0.72rem', color: '#8AA4C8', marginTop: '4px' }}>
                            {p.description}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Request Body Schema */}
              {inspectedEndpoint.request_body_schema && (
                <div>
                  <h4 style={{ fontSize: '0.85rem', color: '#8AA4C8', margin: '0 0 10px 0', textTransform: 'uppercase' }}>
                    Request Body Schema
                  </h4>
                  <pre style={{
                    backgroundColor: '#050D1F',
                    padding: '12px',
                    borderRadius: '6px',
                    fontSize: '0.72rem',
                    color: '#4ADE80',
                    overflowX: 'auto',
                    border: '1px solid rgba(0, 200, 255, 0.15)'
                  }}>
                    {JSON.stringify(inspectedEndpoint.request_body_schema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: AUTHENTICATION & DUAL-PRINCIPAL CONFIGURATION                      */}
      {/* ========================================================================= */}
      {activeTab === 'auth' && selectedTarget && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '900px', margin: '0 auto', width: '100%' }}>
          
          {/* Header Explanation */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '12px',
            border: '1px solid rgba(0, 200, 255, 0.15)',
            padding: '20px 24px'
          }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 6px 0' }}>
              Dual-Principal Authentication Setup (BOLA / IDOR Verification)
            </h2>
            <p style={{ fontSize: '0.84rem', color: '#8AA4C8', margin: 0, lineHeight: 1.45 }}>
              Broken Object Level Authorization (OWASP API1:2023) occurs when an API fails to verify whether the authenticated caller owns the requested object. 
              Configure <strong>User A (Legitimate Owner)</strong> and <strong>User B (Attacker / Probe)</strong>. 
              Member 1's security detection engine tests whether User B can access User A's private resources.
            </p>
          </div>

          {/* Dual Principal Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            
            {/* User A Card */}
            <div style={{
              backgroundColor: '#07182B',
              borderRadius: '12px',
              border: '1px solid rgba(59, 130, 246, 0.35)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#60A5FA',
                    fontWeight: 700
                  }}>
                    A
                  </div>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#F1F5F9', margin: 0 }}>
                      User A (Resource Owner)
                    </h3>
                    <span style={{ fontSize: '0.72rem', color: '#60A5FA' }}>Legitimate Patient / User Account</span>
                  </div>
                </div>

                {authProfiles.some(p => p.account_label === 'User A') && (
                  <span style={{ fontSize: '0.7rem', color: '#4ADE80', backgroundColor: 'rgba(34, 197, 94, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                    Encrypted & Active
                  </span>
                )}
              </div>

              {/* Form A */}
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Auth Type
                </label>
                <select
                  value={userAAuthType}
                  onChange={(e) => setUserAAuthType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#0D223A',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem'
                  }}
                >
                  <option value="bearer">Bearer Token (JWT)</option>
                  <option value="api_key">API Key Header</option>
                  <option value="basic">Basic Auth</option>
                  <option value="none">No Auth (Public)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Header Name
                </label>
                <input
                  type="text"
                  value={userAHeader}
                  onChange={(e) => setUserAHeader(e.target.value)}
                  placeholder="Authorization or X-Api-Key"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Secret Token / Password (Fernet Encrypted)
                </label>
                <input
                  type="password"
                  value={userAToken}
                  onChange={(e) => setUserAToken(e.target.value)}
                  placeholder={authProfiles.some(p => p.account_label === 'User A') ? '•••••••• (Stored securely)' : 'Paste User A credential'}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem',
                    boxSizing: 'border-box',
                    fontFamily: 'monospace'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                    Username
                  </label>
                  <input
                    type="text"
                    value={userAUsername}
                    onChange={(e) => setUserAUsername(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: 'rgba(13, 34, 58, 0.6)',
                      border: '1px solid rgba(0, 200, 255, 0.2)',
                      borderRadius: '6px',
                      color: '#F1F5F9',
                      fontSize: '0.8rem',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                    Owned Resource ID
                  </label>
                  <input
                    type="text"
                    value={userAResourceId}
                    onChange={(e) => setUserAResourceId(e.target.value)}
                    placeholder="e.g. 101"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: 'rgba(13, 34, 58, 0.6)',
                      border: '1px solid rgba(0, 200, 255, 0.2)',
                      borderRadius: '6px',
                      color: '#F1F5F9',
                      fontSize: '0.8rem',
                      boxSizing: 'border-box',
                      fontFamily: 'monospace'
                    }}
                  />
                </div>
              </div>

              <button
                onClick={() => handleSaveAuthProfile('User A')}
                disabled={savingUserA}
                style={{
                  backgroundColor: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  color: '#60A5FA',
                  borderRadius: '6px',
                  padding: '9px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginTop: '6px'
                }}
              >
                {savingUserA ? 'Encrypting & Saving...' : 'Save User A Profile'}
              </button>
            </div>

            {/* User B Card */}
            <div style={{
              backgroundColor: '#07182B',
              borderRadius: '12px',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#F87171',
                    fontWeight: 700
                  }}>
                    B
                  </div>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#F1F5F9', margin: 0 }}>
                      User B (Attacker / Probe)
                    </h3>
                    <span style={{ fontSize: '0.72rem', color: '#F87171' }}>Cross-Tenant Unauthorized Caller</span>
                  </div>
                </div>

                {authProfiles.some(p => p.account_label === 'User B') && (
                  <span style={{ fontSize: '0.7rem', color: '#4ADE80', backgroundColor: 'rgba(34, 197, 94, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                    Encrypted & Active
                  </span>
                )}
              </div>

              {/* Form B */}
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Auth Type
                </label>
                <select
                  value={userBAuthType}
                  onChange={(e) => setUserBAuthType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#0D223A',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem'
                  }}
                >
                  <option value="bearer">Bearer Token (JWT)</option>
                  <option value="api_key">API Key Header</option>
                  <option value="basic">Basic Auth</option>
                  <option value="none">No Auth (Public)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Header Name
                </label>
                <input
                  type="text"
                  value={userBHeader}
                  onChange={(e) => setUserBHeader(e.target.value)}
                  placeholder="Authorization or X-Api-Key"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Secret Token / Password (Fernet Encrypted)
                </label>
                <input
                  type="password"
                  value={userBToken}
                  onChange={(e) => setUserBToken(e.target.value)}
                  placeholder={authProfiles.some(p => p.account_label === 'User B') ? '•••••••• (Stored securely)' : 'Paste User B credential'}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem',
                    boxSizing: 'border-box',
                    fontFamily: 'monospace'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#8AA4C8', marginBottom: '4px' }}>
                  Username
                </label>
                <input
                  type="text"
                  value={userBUsername}
                  onChange={(e) => setUserBUsername(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(13, 34, 58, 0.6)',
                    border: '1px solid rgba(0, 200, 255, 0.2)',
                    borderRadius: '6px',
                    color: '#F1F5F9',
                    fontSize: '0.8rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                onClick={() => handleSaveAuthProfile('User B')}
                disabled={savingUserB}
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#F87171',
                  borderRadius: '6px',
                  padding: '9px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginTop: '6px'
                }}
              >
                {savingUserB ? 'Encrypting & Saving...' : 'Save User B Profile'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: LAUNCH TARGETED SECURITY SCAN                                      */}
      {/* ========================================================================= */}
      {activeTab === 'scan' && selectedTarget && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '880px', margin: '0 auto', width: '100%' }}>
          
          {/* Target Summary Card */}
          <div style={{
            backgroundColor: '#07182B',
            borderRadius: '12px',
            border: '1px solid rgba(0, 200, 255, 0.2)',
            padding: '22px 26px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 4px 0' }}>
                  Targeted Scan Launchpad
                </h3>
                <span style={{ fontSize: '0.84rem', color: '#8AA4C8' }}>
                  Auditing <strong style={{ color: '#F1F5F9' }}>{selectedTarget.name}</strong> ({selectedTarget.base_url})
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={() => {
                    if (setContextTarget) setContextTarget(selectedTarget.id);
                    setActivePage('scans', { targetId: selectedTarget.id, tab: 'new' });
                  }}
                  title="Open in Full Security Scans Workbench"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    backgroundColor: 'rgba(0, 229, 255, 0.12)',
                    border: '1px solid rgba(0, 229, 255, 0.35)',
                    color: '#00E5FF',
                    borderRadius: '6px',
                    padding: '7px 12px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <ExternalLink size={13} />
                  <span>Open in Full Scans Workbench</span>
                </button>
                <button
                  onClick={handleValidateTarget}
                  disabled={validatingTarget}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    backgroundColor: 'rgba(25, 211, 255, 0.1)',
                    border: '1px solid rgba(25, 211, 255, 0.3)',
                    color: '#19D3FF',
                    borderRadius: '6px',
                    padding: '7px 14px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <CheckCircle2 size={14} className={validatingTarget ? 'animate-spin' : ''} />
                  {validatingTarget ? 'Validating...' : 'Test Target Connectivity'}
                </button>
              </div>
            </div>

            {/* Validation result pill */}
            {validationResult && (
              <div style={{
                backgroundColor: validationResult.is_valid ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                border: `1px solid ${validationResult.is_valid ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '0.8rem',
                color: validationResult.is_valid ? '#4ADE80' : '#F87171',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <span>
                  Status: <strong>{validationResult.is_valid ? 'Host Reachable & Safe' : 'Connectivity Warning'}</strong>
                  {' '}(HTTP {validationResult.status_code || 'N/A'}, {validationResult.latency_ms}ms)
                </span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  IP: {validationResult.validated_ip || 'Resolved'}
                </span>
              </div>
            )}

            {/* Readiness Checklist */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
              backgroundColor: 'rgba(13, 34, 58, 0.6)',
              padding: '14px',
              borderRadius: '8px',
              border: '1px solid rgba(0, 200, 255, 0.1)'
            }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#6482A6' }}>Target Operations</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38BDF8', marginTop: '2px' }}>
                  {selectedTarget.selected_endpoint_count || 0} / {selectedTarget.endpoint_count || 0} Selected
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#6482A6' }}>Dual Principals</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: authProfiles.length >= 2 ? '#4ADE80' : '#FBBF24', marginTop: '2px' }}>
                  {authProfiles.length >= 2 ? 'Both A & B Ready' : `${authProfiles.length}/2 Configured`}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#6482A6' }}>SSRF Defense</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#4ADE80', marginTop: '2px' }}>
                  Pinned Socket Active
                </div>
              </div>
            </div>

            {/* Scan Categories Selection */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#8AA4C8', marginBottom: '8px' }}>
                Active Security Audit Categories:
              </label>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {[
                  { id: 'BOLA', label: 'BOLA / IDOR Verification' },
                  { id: 'AUTH', label: 'Authentication Checks' },
                  { id: 'HEADERS', label: 'Security Headers' },
                  { id: 'CONFIG', label: 'API Configuration' },
                ].map(c => {
                  const isChecked = scanCategories.includes(c.id);
                  return (
                    <label
                      key={c.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 14px',
                        borderRadius: '6px',
                        backgroundColor: isChecked ? 'rgba(25, 211, 255, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                        border: isChecked ? '1px solid #19D3FF' : '1px solid rgba(255, 255, 255, 0.1)',
                        color: isChecked ? '#19D3FF' : '#94A3B8',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          setScanCategories(prev => 
                            prev.includes(c.id) ? prev.filter(x => x !== c.id) : [...prev, c.id]
                          );
                        }}
                      />
                      {c.label}
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Authorization Checkbox */}
            <div style={{
              backgroundColor: 'rgba(13, 34, 58, 0.6)',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid rgba(0, 200, 255, 0.12)'
            }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.82rem', color: '#F1F5F9' }}>
                <input
                  type="checkbox"
                  checked={userAuthorized}
                  onChange={(e) => setUserAuthorized(e.target.checked)}
                  style={{ width: '16px', height: '16px' }}
                />
                <span>
                  I confirm I am authorized to perform security testing against <strong>{selectedTarget.base_url}</strong>.
                </span>
              </label>
            </div>

            {/* Launch Button */}
            <button
              onClick={handleLaunchScan}
              disabled={isLaunchingScan || !userAuthorized}
              style={{
                backgroundColor: isLaunchingScan || !userAuthorized ? '#334155' : '#19D3FF',
                border: 'none',
                color: isLaunchingScan || !userAuthorized ? '#94A3B8' : '#050D1F',
                borderRadius: '8px',
                padding: '14px 28px',
                fontSize: '0.95rem',
                fontWeight: 700,
                cursor: isLaunchingScan || !userAuthorized ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                transition: 'all 0.2s ease',
                boxShadow: isLaunchingScan || !userAuthorized ? 'none' : '0 0 20px rgba(25, 211, 255, 0.3)'
              }}
            >
              {isLaunchingScan ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Executing Security Engine Probes...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Launch Security Scan Now
                </>
              )}
            </button>
          </div>

          {/* Terminal Logs Window */}
          {scanTerminalLogs.length > 0 && (
            <div style={{
              backgroundColor: '#050D1F',
              borderRadius: '10px',
              border: '1px solid rgba(0, 200, 255, 0.2)',
              padding: '16px',
              fontFamily: 'monospace',
              fontSize: '0.78rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: '#6482A6', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '6px' }}>
                <Terminal size={14} />
                <span>Security Engine Execution Logs</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {scanTerminalLogs.map((log, i) => (
                  <div key={i} style={{ color: log.includes('[ERROR]') ? '#F87171' : log.includes('[COMPLETE]') ? '#4ADE80' : '#8AA4C8' }}>
                    {log}
                  </div>
                ))}
              </div>

              {scanLaunchResult && (
                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => {
                      selectScan(scanLaunchResult.id);
                      setActivePage('findings');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      backgroundColor: '#19D3FF',
                      border: 'none',
                      color: '#050D1F',
                      borderRadius: '6px',
                      padding: '8px 16px',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    View Discovered Vulnerabilities
                    <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SparklesIcon(props) {
  return (
    <svg
      width={props.size || 16}
      height={props.size || 16}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={props.className}
      style={props.style}
    >
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}

export default function ApiOnboarding(props) {
  return (
    <ErrorBoundary title="API Onboarding & Discovery Error">
      <ApiOnboardingContent {...props} />
    </ErrorBoundary>
  );
}
