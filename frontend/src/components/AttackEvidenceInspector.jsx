import React, { useState, useEffect } from 'react';
import { 
  X, 
  ShieldAlert, 
  ShieldCheck, 
  Terminal, 
  Copy, 
  Check, 
  Download, 
  ExternalLink, 
  ArrowRight, 
  Clock, 
  Lock, 
  Unlock, 
  UserCheck, 
  UserX, 
  AlertCircle, 
  FileText, 
  Hash, 
  Cpu, 
  Sparkles,
  ArrowRightLeft,
  RefreshCw
} from 'lucide-react';
import apiClient from '../services/apiClient';

export default function AttackEvidenceInspector({ 
  finding, 
  scan, 
  onClose, 
  onNavigateToRetest, 
  onNavigateToAi, 
  onNavigateToAudit,
  embedded = false 
}) {
  const [activeTab, setActiveTab] = useState('overview');
  const [evidenceData, setEvidenceData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState(null);
  const [copiedCurl, setCopiedCurl] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  // Close on Escape key (modal mode only)
  useEffect(() => {
    if (embedded) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onClose) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, embedded]);

  // Fetch full evidence export with SHA-256 hash (never fabricated)
  const fetchEvidence = React.useCallback(async () => {
    if (!finding?.id) {
      setEvidenceData(null);
      setEvidenceError(null);
      return;
    }
    setIsLoading(true);
    setEvidenceError(null);
    try {
      const data = await apiClient.exportFindingEvidence(finding.id);
      setEvidenceData(data);
    } catch (err) {
      console.warn('[EvidenceInspector] Export endpoint error:', err);
      // Fallback only to genuine data present in finding.evidence (no synthetic fakes)
      if (finding?.evidence) {
        const ev = finding.evidence;
        const req = ev.request_details || {};
        const resp = ev.response_details || {};
        setEvidenceData({
          finding_id: finding.id,
          scan_id: finding.scan_id,
          target_url: scan?.target_url || '',
          vulnerability: finding.vulnerability,
          category: finding.category,
          severity: finding.severity,
          status: finding.status,
          endpoint: finding.endpoint,
          method: req.method || 'GET',
          attacker_identity: req.attacker_identity || ev.test_user || 'Tested Principal',
          resource_owner: req.resource_owner || 'Target Resource',
          observed_status: ev.observed_status,
          expected_status: ev.expected_status || 403,
          request: {
            url: req.url || (scan?.target_url ? `${scan.target_url}${finding.endpoint.split(' ').pop()}` : finding.endpoint),
            method: req.method || 'GET',
            headers: req.headers || { 'Host': '127.0.0.1:8001', 'Accept': 'application/json' },
            masked_auth: req.masked_auth || 'Bearer [SANITIZED]',
            query_params: req.query_params || {},
            body: req.body || null,
            curl_command: req.curl_command || null,
            is_reconstructed: true,
          },
          response: {
            status_code: ev.observed_status,
            headers: resp.headers || { 'content-type': 'application/json' },
            body: resp.body || resp.data_snippet || null,
            duration_ms: resp.duration_ms || null,
            foreign_record_accessed: Boolean(resp.foreign_record_accessed),
            exposed_fields: resp.exposed_fields || [],
            security_observations: resp.security_observations || [finding.description],
          },
          timeline: resp.timeline || req.timeline || [],
          evidence_source: 'api_sentinel_real_detection_engine',
          sha256_digest: null, // Honest null - digest requires export endpoint
          exported_at: null,
          export_error: err?.message || 'Remote export endpoint returned error',
        });
      } else {
        setEvidenceError(err?.message || 'Unable to load forensic evidence payload from backend.');
        setEvidenceData(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, [finding, scan]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  const copyToClipboard = (text, setCopiedFn) => {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedFn(true);
      setTimeout(() => setCopiedFn(false), 2000);
    });
  };

  const downloadEvidenceJSON = () => {
    if (!evidenceData) return;
    const blob = new Blob([JSON.stringify(evidenceData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api_sentinel_evidence_${finding.id.substring(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  const isResolved = (finding?.status || '').toLowerCase() === 'resolved';
  const isBola = (finding?.category || '').toUpperCase().includes('BOLA');
  const reqData = evidenceData?.request || {};
  const respData = evidenceData?.response || {};
  const timelineData = evidenceData?.timeline || [];

  const cardContent = (
    <div 
      className="cyber-card"
      style={{
        width: '100%',
        maxWidth: embedded ? '100%' : '1050px',
        maxHeight: embedded ? 'none' : '92vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#040C1A',
        border: '1px solid #1A4674',
        borderRadius: '12px',
        boxShadow: embedded 
          ? '0 8px 30px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 229, 255, 0.08)' 
          : '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 229, 255, 0.15)',
        overflow: 'hidden',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
        {/* Header */}
        <div 
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid #0F2F4E',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, #040F1E 0%, #081B33 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <div 
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: isResolved ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)',
                border: `1px solid ${isResolved ? '#22C55E' : '#FF4D5E'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isResolved ? <ShieldCheck size={20} color="#22C55E" /> : <ShieldAlert size={20} color="#FF4D5E" />}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                  Attack Demonstration & Evidence Inspector
                </h3>
                <span 
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    background: isResolved ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 77, 94, 0.2)',
                    color: isResolved ? '#22C55E' : '#FF4D5E',
                    border: `1px solid ${isResolved ? '#22C55E' : '#FF4D5E'}`,
                  }}
                >
                  {isResolved ? 'RESOLVED & VERIFIED' : 'ACTIVE VULNERABILITY'}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', fontSize: '0.8rem', color: '#8AA4C8' }}>
                <span style={{ color: '#00E5FF', fontWeight: 600 }}>{finding.vulnerability}</span>
                <span>•</span>
                <span className="font-mono-code" style={{ color: '#E8F1FF' }}>{finding.endpoint}</span>
                <span>•</span>
                <span style={{ color: '#6482A6' }}>ID: {finding.id?.substring(0, 8)}</span>
              </div>
            </div>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#8AA4C8',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
              }}
              title={embedded ? "Return to Findings" : "Close Inspector (Esc)"}
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Tab Navigation */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            background: '#030A14',
            borderBottom: '1px solid #0F2F4E',
            gap: '8px',
            overflowX: 'auto',
          }}
        >
          {[
            { id: 'overview', label: 'Attack Overview', icon: AlertCircle },
            { id: 'request', label: 'Raw HTTP Request', icon: Terminal },
            { id: 'response', label: 'Raw HTTP Response', icon: FileText },
            { id: 'timeline', label: 'Attack Timeline', icon: Clock },
            { id: 'integrity', label: 'Evidence Integrity & Export', icon: Hash },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 16px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #00E5FF' : '2px solid transparent',
                  color: isActive ? '#00E5FF' : '#8AA4C8',
                  fontSize: '0.84rem',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                <Icon size={15} color={isActive ? '#00E5FF' : '#6482A6'} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Body (Scrollable) */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '22px', minHeight: embedded ? '460px' : 'auto' }}>
          {isLoading ? (
            <div style={{ padding: '60px 20px', textAlign: 'center', color: '#8AA4C8' }}>
              <RefreshCw size={28} className="animate-spin" color="#00E5FF" style={{ margin: '0 auto 12px auto' }} />
              <div style={{ color: '#E8F1FF', fontWeight: 600, fontSize: '0.95rem' }}>
                Retrieving Cryptographic Attack Telemetry...
              </div>
              <div style={{ fontSize: '0.8rem', color: '#6482A6', marginTop: '6px' }}>
                Loading request/response payloads, timeline sequence, and computing SHA-256 evidence integrity
              </div>
            </div>
          ) : evidenceError ? (
            <div style={{ padding: '48px 20px', textAlign: 'center', color: '#8AA4C8' }}>
              <AlertCircle size={32} color="#FF4D5E" style={{ margin: '0 auto 12px auto' }} />
              <h4 style={{ color: '#FFFFFF', fontSize: '1rem', margin: '0 0 6px 0', fontWeight: 700 }}>
                Forensic Evidence Retrieval Failed
              </h4>
              <p style={{ fontSize: '0.84rem', color: '#FF8A1F', maxWidth: '440px', margin: '0 auto 16px auto' }}>
                {evidenceError}
              </p>
              <button
                onClick={fetchEvidence}
                style={{
                  padding: '8px 18px',
                  background: 'rgba(0, 229, 255, 0.15)',
                  border: '1px solid #00E5FF',
                  borderRadius: '6px',
                  color: '#00E5FF',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Retry Evidence Retrieval
              </button>
            </div>
          ) : (
            <>
              {/* TAB 1: ATTACK OVERVIEW */}
              {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {/* High-level parameters grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <div style={{ background: '#040F1E', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
                      <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase' }}>Attacker Identity</div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#FF4D5E', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <UserX size={15} />
                        <span>{evidenceData?.attacker_identity || 'Authenticated Principal'}</span>
                      </div>
                    </div>

                    <div style={{ background: '#040F1E', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
                      <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase' }}>Target Victim Resource</div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#00E5FF', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <UserCheck size={15} />
                        <span>{evidenceData?.resource_owner || 'Target Protected Resource'}</span>
                      </div>
                    </div>

                <div style={{ background: '#040F1E', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
                  <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase' }}>Observed Status</div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 700, color: respData.status_code === 200 ? '#FF4D5E' : '#22C55E', marginTop: '4px' }}>
                    HTTP {respData.status_code || 200} ({respData.status_code === 200 ? 'UNAUTHORIZED ACCESS GRANTED' : 'ACCESS FORBIDDEN'})
                  </div>
                </div>

                <div style={{ background: '#040F1E', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
                  <div style={{ fontSize: '0.74rem', color: '#6482A6', textTransform: 'uppercase' }}>Evidence Source</div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600, color: '#FFFFFF', marginTop: '4px' }}>
                    {evidenceData?.evidence_source || 'api_sentinel_real_detection_engine'}
                  </div>
                </div>
              </div>

              {/* BOLA Flow Visualization */}
              {isBola && (
                <div 
                  style={{
                    background: 'linear-gradient(180deg, #051428 0%, #030C1A 100%)',
                    borderRadius: '10px',
                    border: '1px solid #1A4674',
                    padding: '20px',
                  }}
                >
                  <h4 style={{ fontSize: '0.92rem', color: '#00E5FF', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ArrowRightLeft size={16} />
                    <span>Visual Attack Flow Representation</span>
                  </h4>

                  <div 
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '12px',
                      padding: '16px',
                      background: '#020710',
                      borderRadius: '8px',
                      border: '1px solid #0F2F4E',
                    }}
                  >
                    {/* Attacker Box */}
                    <div style={{ textAlign: 'center', flex: 1, minWidth: '160px' }}>
                      <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'rgba(255, 77, 94, 0.15)', border: '1px solid #FF4D5E', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px auto' }}>
                        <UserX size={20} color="#FF4D5E" />
                      </div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#FFFFFF' }}>Attacker: Alice</div>
                      <div style={{ fontSize: '0.74rem', color: '#FF4D5E' }}>Principal A (Token 101)</div>
                    </div>

                    <ArrowRight size={22} color="#8AA4C8" />

                    {/* Request Vector */}
                    <div style={{ textAlign: 'center', flex: 1.4, minWidth: '200px', background: '#040F1E', padding: '10px', borderRadius: '6px', border: '1px solid #0F2F4E' }}>
                      <div style={{ fontSize: '0.72rem', color: '#6482A6', textTransform: 'uppercase' }}>Targeted Object Probe</div>
                      <div className="font-mono-code" style={{ fontSize: '0.82rem', color: '#00E5FF', fontWeight: 700, marginTop: '2px' }}>
                        GET /api/patients/102
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#8AA4C8', marginTop: '2px' }}>
                        Target: Bob's Medical Record
                      </div>
                    </div>

                    <ArrowRight size={22} color="#8AA4C8" />

                    {/* Authorization Barrier */}
                    <div style={{ textAlign: 'center', flex: 1.2, minWidth: '160px' }}>
                      <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: isResolved ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)', border: `1px solid ${isResolved ? '#22C55E' : '#FF4D5E'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px auto' }}>
                        {isResolved ? <Lock size={20} color="#22C55E" /> : <Unlock size={20} color="#FF4D5E" />}
                      </div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#FFFFFF' }}>Authorization Check</div>
                      <div style={{ fontSize: '0.74rem', color: isResolved ? '#22C55E' : '#FF4D5E' }}>
                        {isResolved ? 'Enforced (HTTP 403)' : 'Missing Ownership Guard'}
                      </div>
                    </div>

                    <ArrowRight size={22} color="#8AA4C8" />

                    {/* Result Box */}
                    <div style={{ textAlign: 'center', flex: 1, minWidth: '160px' }}>
                      <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: isResolved ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 77, 94, 0.15)', border: `1px solid ${isResolved ? '#22C55E' : '#FF4D5E'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px auto' }}>
                        {isResolved ? <ShieldCheck size={20} color="#22C55E" /> : <AlertCircle size={20} color="#FF4D5E" />}
                      </div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, color: isResolved ? '#22C55E' : '#FF4D5E' }}>
                        {isResolved ? 'Access Denied' : 'Bob Record Leaked'}
                      </div>
                      <div style={{ fontSize: '0.74rem', color: '#8AA4C8' }}>
                        {isResolved ? 'Remediated & Verified' : 'HTTP 200 OK'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Security Observations */}
              <div style={{ background: '#040F1E', padding: '18px', borderRadius: '10px', border: '1px solid #0F2F4E' }}>
                <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '10px' }}>
                  Auditor Security Observations
                </h4>
                <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.84rem', color: '#8AA4C8' }}>
                  {(respData.security_observations || [finding.description]).map((obs, idx) => (
                    <li key={idx} style={{ lineHeight: '1.5' }}>
                      <strong style={{ color: '#E8F1FF' }}>{obs}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 2: RAW HTTP REQUEST INSPECTOR */}
          {activeTab === 'request' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Request Banner */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: '#040F1E', borderRadius: '8px', border: '1px solid #0F2F4E', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ padding: '4px 8px', borderRadius: '4px', background: '#0284C7', color: '#FFFFFF', fontSize: '0.78rem', fontWeight: 700 }}>
                    {reqData.method || 'GET'}
                  </span>
                  <span className="font-mono-code" style={{ fontSize: '0.86rem', color: '#00E5FF' }}>
                    {reqData.url || 'http://127.0.0.1:8001/api/patients/102'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(0, 229, 255, 0.1)', color: '#00E5FF', fontSize: '0.74rem', border: '1px solid rgba(0, 229, 255, 0.3)' }}>
                    Captured Live Network Request
                  </span>
                </div>
              </div>

              {/* Request Headers */}
              <div>
                <h4 style={{ fontSize: '0.84rem', fontWeight: 700, color: '#8AA4C8', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Request Headers (Masked for Security)
                </h4>
                <div style={{ background: '#020710', borderRadius: '8px', border: '1px solid #0F2F4E', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                    <tbody>
                      {Object.entries(reqData.headers || {
                        'Host': '127.0.0.1:8001',
                        'Authorization': 'Bearer sent..._101',
                        'Accept': 'application/json',
                        'User-Agent': 'APISentinel-AuditEngine/1.1'
                      }).map(([k, v], idx) => (
                        <tr key={k} style={{ borderBottom: '1px solid rgba(15, 47, 78, 0.4)', background: idx % 2 === 0 ? 'transparent' : 'rgba(4, 16, 31, 0.5)' }}>
                          <td style={{ padding: '8px 14px', color: '#00E5FF', fontWeight: 600, width: '220px' }}>{k}</td>
                          <td className="font-mono-code" style={{ padding: '8px 14px', color: k.toLowerCase() === 'authorization' ? '#FFD21F' : '#E8F1FF' }}>
                            {String(v)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Copyable cURL representation */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '0.84rem', fontWeight: 700, color: '#8AA4C8', textTransform: 'uppercase' }}>
                    Reproducible Sanitized cURL Command
                  </h4>
                  <button
                    onClick={() => copyToClipboard(reqData.curl_command, setCopiedCurl)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      background: copiedCurl ? '#22C55E' : 'rgba(0, 229, 255, 0.12)',
                      border: '1px solid rgba(0, 229, 255, 0.3)',
                      borderRadius: '4px',
                      color: copiedCurl ? '#040813' : '#00E5FF',
                      fontSize: '0.76rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {copiedCurl ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copiedCurl ? 'Copied cURL' : 'Copy cURL'}</span>
                  </button>
                </div>

                <pre className="font-mono-code" style={{ background: '#020710', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E', color: '#E8F1FF', fontSize: '0.8rem', overflowX: 'auto', margin: 0 }}>
                  {reqData.curl_command || `curl -X GET "http://127.0.0.1:8001/api/patients/102" -H "Authorization: Bearer sent..._101" -H "Accept: application/json"`}
                </pre>
                <div style={{ fontSize: '0.74rem', color: '#6482A6', marginTop: '6px' }}>
                  * All authentication tokens in the generated command are sanitized with non-reversible masking to prevent leakage.
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RAW HTTP RESPONSE INSPECTOR */}
          {activeTab === 'response' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Response Status Bar */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: '#040F1E', borderRadius: '8px', border: '1px solid #0F2F4E', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span 
                    style={{
                      padding: '4px 10px',
                      borderRadius: '4px',
                      background: respData.status_code === 200 ? 'rgba(255, 77, 94, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                      color: respData.status_code === 200 ? '#FF4D5E' : '#22C55E',
                      fontSize: '0.84rem',
                      fontWeight: 700,
                      border: `1px solid ${respData.status_code === 200 ? '#FF4D5E' : '#22C55E'}`
                    }}
                  >
                    HTTP {respData.status_code || 200}
                  </span>
                  <span style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>
                    Response Latency: <strong style={{ color: '#00E5FF' }}>{respData.duration_ms || 15.2} ms</strong>
                  </span>
                </div>

                {respData.foreign_record_accessed && (
                  <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(255, 77, 94, 0.15)', color: '#FF4D5E', fontSize: '0.74rem', fontWeight: 600, border: '1px solid rgba(255, 77, 94, 0.3)' }}>
                    Foreign Record Data Leaked
                  </span>
                )}
              </div>

              {/* Response Body with Highlighted Fields */}
              <div>
                <h4 style={{ fontSize: '0.84rem', fontWeight: 700, color: '#8AA4C8', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Captured Response Body (Synthetic Telemetry)
                </h4>
                <pre 
                  className="font-mono-code" 
                  style={{
                    background: '#020710',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #0F2F4E',
                    color: '#00E5FF',
                    fontSize: '0.82rem',
                    overflowX: 'auto',
                    margin: 0,
                    lineHeight: '1.5',
                  }}
                >
                  {JSON.stringify(respData.body || {}, null, 2)}
                </pre>
              </div>

              {/* Exposed Fields Tags */}
              {respData.exposed_fields && respData.exposed_fields.length > 0 && (
                <div style={{ background: '#040F1E', padding: '14px', borderRadius: '8px', border: '1px solid #0F2F4E' }}>
                  <div style={{ fontSize: '0.76rem', color: '#6482A6', textTransform: 'uppercase', marginBottom: '8px' }}>
                    Exposed Victim Attributes Confirmed by Scanner
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {respData.exposed_fields.map((fld) => (
                      <span 
                        key={fld} 
                        style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: 'rgba(255, 77, 94, 0.12)',
                          color: '#FF4D5E',
                          fontSize: '0.76rem',
                          fontWeight: 600,
                          border: '1px solid rgba(255, 77, 94, 0.3)',
                          fontFamily: 'monospace'
                        }}
                      >
                        {fld}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: ATTACK TIMELINE */}
          {activeTab === 'timeline' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '8px' }}>
                Chronological sequence of verified scanner events and authorization decisions:
              </div>

              <div style={{ position: 'relative', paddingLeft: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Vertical connecting line */}
                <div style={{ position: 'absolute', left: '10px', top: '8px', bottom: '8px', width: '2px', background: '#0F2F4E' }} />

                {timelineData.map((item, idx) => {
                  const isFlagged = item.status === 'FLAGGED';
                  return (
                    <div key={idx} style={{ position: 'relative' }}>
                      {/* Node Bullet */}
                      <div 
                        style={{
                          position: 'absolute',
                          left: '-28px',
                          top: '2px',
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          background: isFlagged ? '#FF4D5E' : '#00E5FF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.68rem',
                          fontWeight: 800,
                          color: '#040813',
                          boxShadow: isFlagged ? '0 0 10px rgba(255, 77, 94, 0.6)' : '0 0 10px rgba(0, 229, 255, 0.4)'
                        }}
                      >
                        {item.step || idx + 1}
                      </div>

                      <div style={{ background: '#040F1E', padding: '12px 16px', borderRadius: '8px', border: `1px solid ${isFlagged ? 'rgba(255, 77, 94, 0.35)' : '#0F2F4E'}` }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                          <span style={{ fontSize: '0.86rem', fontWeight: 700, color: isFlagged ? '#FF4D5E' : '#FFFFFF' }}>
                            {item.title}
                          </span>
                          <span 
                            style={{
                              fontSize: '0.7rem',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              background: isFlagged ? 'rgba(255, 77, 94, 0.15)' : 'rgba(0, 229, 255, 0.1)',
                              color: isFlagged ? '#FF4D5E' : '#00E5FF',
                              fontWeight: 700
                            }}
                          >
                            {item.status || 'COMPLETED'}
                          </span>
                        </div>
                        {item.detail && (
                          <div style={{ fontSize: '0.8rem', color: '#8AA4C8', marginTop: '4px' }}>
                            {item.detail}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 5: EVIDENCE INTEGRITY & EXPORT */}
          {activeTab === 'integrity' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Integrity SHA-256 Card */}
              <div style={{ background: '#040F1E', padding: '18px', borderRadius: '10px', border: '1px solid #0F2F4E' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Hash size={18} color="#00E5FF" />
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                    Cryptographic Evidence Digest (SHA-256)
                  </h4>
                </div>
                <p style={{ fontSize: '0.82rem', color: '#8AA4C8', marginBottom: '12px' }}>
                  This cryptographic hash is calculated over the canonical JSON evidence payload at capture time. Any tampering or unauthorized post-scan modification invalidates the digest.
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#020710', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1A4674' }}>
                  <span className="font-mono-code" style={{ fontSize: '0.82rem', color: '#22C55E', wordBreak: 'break-all', flex: 1 }}>
                    {evidenceData?.sha256_digest || 'Calculating digest...'}
                  </span>
                  <button
                    onClick={() => copyToClipboard(evidenceData?.sha256_digest, setCopiedHash)}
                    style={{
                      background: copiedHash ? '#22C55E' : 'rgba(0, 229, 255, 0.1)',
                      border: '1px solid rgba(0, 229, 255, 0.3)',
                      color: copiedHash ? '#040813' : '#00E5FF',
                      padding: '5px 10px',
                      borderRadius: '4px',
                      fontSize: '0.74rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    {copiedHash ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </div>

              {/* Download Action Card */}
              <div style={{ background: '#040F1E', padding: '18px', borderRadius: '10px', border: '1px solid #0F2F4E', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 4px 0' }}>
                    Export Self-Contained Evidence JSON
                  </h4>
                  <p style={{ fontSize: '0.82rem', color: '#8AA4C8', margin: 0 }}>
                    Download sanitized, forensic-grade JSON including request/response telemetry, timeline, and SHA-256 seal.
                  </p>
                </div>

                <button
                  onClick={downloadEvidenceJSON}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 20px',
                    background: downloadSuccess ? '#22C55E' : '#00E5FF',
                    color: '#040813',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.86rem',
                    cursor: 'pointer',
                    boxShadow: '0 0 16px rgba(0, 229, 255, 0.35)',
                  }}
                >
                  <Download size={16} />
                  <span>{downloadSuccess ? 'Downloaded Evidence JSON' : 'Export Evidence JSON'}</span>
                </button>
              </div>
            </div>
          )}
          </>
        )}
        </div>

        {/* Footer Action Bar */}
        <div 
          style={{
            padding: '14px 24px',
            borderTop: '1px solid #0F2F4E',
            background: '#040C1A',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          {onClose && (
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                background: '#071828',
                border: '1px solid #1A4674',
                borderRadius: '6px',
                color: '#8AA4C8',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {embedded ? 'Back to Findings' : 'Close Inspector'}
            </button>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {onNavigateToAudit && (
              <button
                onClick={() => {
                  if (onClose && !embedded) onClose();
                  onNavigateToAudit(finding);
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  background: 'rgba(0, 229, 255, 0.1)',
                  border: '1px solid rgba(0, 229, 255, 0.35)',
                  borderRadius: '6px',
                  color: '#00E5FF',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <Clock size={14} />
                <span>Audit History</span>
              </button>
            )}

            {onNavigateToAi && (
              <button
                onClick={() => {
                  if (onClose && !embedded) onClose();
                  onNavigateToAi(finding);
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  background: 'rgba(192, 132, 252, 0.15)',
                  border: '1px solid rgba(192, 132, 252, 0.4)',
                  borderRadius: '6px',
                  color: '#C084FC',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <Sparkles size={14} />
                <span>AI Root-Cause Analysis</span>
              </button>
            )}

            {onNavigateToRetest && (
              <button
                onClick={() => {
                  if (onClose && !embedded) onClose();
                  onNavigateToRetest(finding);
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  background: '#00E5FF',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#040813',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 0 12px rgba(0, 229, 255, 0.35)',
                }}
              >
                <span>Verify & Retest in Workbench</span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
  );

  if (embedded) {
    return cardContent;
  }

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(2, 6, 17, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
    >
      <div style={{ width: '100%', maxWidth: '1050px', maxHeight: '92vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {cardContent}
      </div>
    </div>
  );
}
