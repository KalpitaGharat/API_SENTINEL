import React, { useState, useEffect } from 'react';
import { Download, FileText, CheckCircle2, ShieldAlert, ShieldCheck, RefreshCw, AlertTriangle, ArrowRight } from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function ReportsContent({ setActivePage }) {
  const { scans, selectedScanId, selectScan } = useScanContext();
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedScanId) {
      setReportData(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    apiClient.getScanReport(selectedScanId)
      .then((data) => {
        if (isMounted) {
          setReportData(data);
        }
      })
      .catch((err) => {
        console.error('[Reports] Failed to fetch report:', err);
        if (isMounted) {
          setError(err?.details?.detail || err?.message || 'Failed to generate security audit report.');
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedScanId]);

  const downloadReportJSON = () => {
    if (!reportData) return;
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api_sentinel_report_${reportData.scan?.id?.substring(0, 8) || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadReportMarkdown = () => {
    if (!reportData) return;
    const s = reportData.scan;
    const sum = reportData.summary;
    let md = `# API SENTINEL SECURITY AUDIT REPORT\n\n`;
    md += `**Target URL:** ${s.target_url}\n`;
    md += `**Scan ID:** \`${s.id}\`\n`;
    md += `**Scan Date:** ${s.created_at}\n`;
    md += `**Status:** ${s.status}\n`;
    md += `**Total Findings:** ${sum.total_findings} (Open: ${sum.open_count}, Resolved: ${sum.resolved_count})\n\n`;
    md += `## Executive Summary\n\n`;
    md += `| OWASP Category | Finding Count |\n| :--- | :--- |\n`;
    for (const [k, v] of Object.entries(sum.category_breakdown || {})) {
      md += `| ${k} | ${v} |\n`;
    }
    md += `\n| Severity Level | Finding Count |\n| :--- | :--- |\n`;
    for (const [k, v] of Object.entries(sum.severity_breakdown || {})) {
      md += `| ${k} | ${v} |\n`;
    }
    md += `\n---\n\n## Detailed Vulnerability Findings\n\n`;
    for (const f of reportData.findings || []) {
      md += `### [${f.severity.toUpperCase()}] ${f.vulnerability}\n\n`;
      md += `- **Endpoint:** \`${f.endpoint}\`\n`;
      md += `- **Category:** \`${f.category}\`\n`;
      md += `- **Status:** **${f.status}**\n`;
      md += `- **Description:** ${f.description}\n`;
      md += `- **Recommendation:** ${f.recommendation}\n\n`;
      if (f.evidence) {
        md += `#### Technical Evidence (Sanitized)\n\`\`\`json\n${JSON.stringify(f.evidence, null, 2)}\n\`\`\`\n\n`;
      }
      if (f.ai_explanation) {
        md += `#### AI Explanation & Root Cause Analysis (${f.ai_explanation.model_name})\n\n`;
        md += `${f.ai_explanation.explanation}\n\n`;
        md += `**Business & Security Impact:**\n${f.ai_explanation.impact}\n\n`;
        md += `**Step-by-Step Remediation:**\n${f.ai_explanation.remediation}\n\n`;
      }
      md += `---\n\n`;
    }
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api_sentinel_report_${s.id?.substring(0, 8) || 'export'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const summary = reportData?.summary || {
    total_findings: 0,
    open_count: 0,
    resolved_count: 0,
    severity_breakdown: {},
    category_breakdown: {},
  };

  const total = summary.total_findings || 0;
  const resolved = summary.resolved_count || 0;
  const open = summary.open_count || 0;
  const remediationRate = total > 0 ? Math.round((resolved / total) * 100) : 100;

  // Calculate dynamic security health score
  const crit = summary.severity_breakdown?.Critical || 0;
  const high = summary.severity_breakdown?.High || 0;
  const med = summary.severity_breakdown?.Medium || 0;
  const low = summary.severity_breakdown?.Low || 0;
  const calculatedHealth = Math.max(10, Math.min(100, Math.round(100 - (crit * 25 + high * 15 + med * 8 + low * 3) + (resolved * 10))));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Bar */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '18px 24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px' 
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '4px' }}>
            Executive Security & Compliance Audit
          </h3>
          <p style={{ color: '#8AA4C8', fontSize: '0.84rem' }}>
            Aggregated vulnerability findings, OWASP compliance matrices, and remediation metrics.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Scan Selector */}
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
              minWidth: '220px',
            }}
          >
            {scans.length === 0 && <option value="">No Scans Available</option>}
            {scans.map((s) => (
              <option key={s.id} value={s.id}>
                {s.target_url} ({s.id.substring(0, 8)})
              </option>
            ))}
          </select>

          <button
            onClick={downloadReportJSON}
            disabled={!reportData || isLoading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 16px',
              background: reportData ? '#00E5FF' : '#0F2F4E',
              color: reportData ? '#040813' : '#8AA4C8',
              border: 'none',
              borderRadius: '8px',
              fontSize: '0.84rem',
              fontWeight: 700,
              cursor: reportData ? 'pointer' : 'not-allowed',
              boxShadow: reportData ? '0 0 16px rgba(0, 229, 255, 0.4)' : 'none',
            }}
          >
            <Download size={15} />
            <span>Export Audit JSON</span>
          </button>

          <button
            onClick={downloadReportMarkdown}
            disabled={!reportData || isLoading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 16px',
              background: reportData ? '#0F2F4E' : '#071828',
              color: reportData ? '#00E5FF' : '#54718C',
              border: '1px solid #1A4674',
              borderRadius: '8px',
              fontSize: '0.84rem',
              fontWeight: 700,
              cursor: reportData ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
            }}
          >
            <FileText size={15} />
            <span>Export Audit Markdown</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="cyber-card" style={{ padding: '50px', textAlign: 'center', color: '#8AA4C8' }}>
          <RefreshCw size={26} className="animate-spin" color="#00E5FF" style={{ margin: '0 auto 12px auto' }} />
          <div>Compiling security audit report from database...</div>
        </div>
      ) : error ? (
        <div className="cyber-card" style={{ padding: '30px', color: '#FF4D5E', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={24} />
          <span>{error}</span>
        </div>
      ) : !reportData ? (
        <div className="cyber-card" style={{ padding: '40px', textAlign: 'center', color: '#8AA4C8' }}>
          <p>No scan selected. Select a scan session above to generate an audit report.</p>
        </div>
      ) : (
        <>
          {/* Overview Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px' }}>
            <div className="cyber-card" style={{ padding: '20px' }}>
              <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase' }}>Security Posture Score</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: calculatedHealth >= 70 ? '#22C55E' : '#FF8A1F', marginTop: '6px' }}>
                {calculatedHealth}/100
              </div>
              <span style={{ fontSize: '0.74rem', color: '#6482A6' }}>
                {calculatedHealth >= 70 ? 'Acceptable Risk Threshold' : 'Remediation Required'}
              </span>
            </div>

            <div className="cyber-card" style={{ padding: '20px' }}>
              <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase' }}>Total Findings</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#FFFFFF', marginTop: '6px' }}>
                {total}
              </div>
              <span style={{ fontSize: '0.74rem', color: '#6482A6' }}>Across all audited endpoints</span>
            </div>

            <div className="cyber-card" style={{ padding: '20px' }}>
              <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase' }}>Remediated & Verified</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#22C55E', marginTop: '6px' }}>
                {resolved}
              </div>
              <span style={{ fontSize: '0.74rem', color: '#22C55E' }}>Confirmed via Retest Probes</span>
            </div>

            <div className="cyber-card" style={{ padding: '20px' }}>
              <span style={{ fontSize: '0.76rem', color: '#8AA4C8', textTransform: 'uppercase' }}>Open Vulnerabilities</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: open > 0 ? '#FF4D5E' : '#22C55E', marginTop: '6px' }}>
                {open}
              </div>
              <span style={{ fontSize: '0.74rem', color: open > 0 ? '#FF4D5E' : '#6482A6' }}>
                {open > 0 ? 'Requires Engineer Attention' : 'All Mitigated'}
              </span>
            </div>
          </div>

          {/* Grids: OWASP Matrix & Severity Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '22px' }}>
            {/* OWASP Matrix */}
            <div className="cyber-card" style={{ padding: '24px' }}>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '16px' }}>
                OWASP API Security Top 10 Category Distribution
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {Object.keys(summary.category_breakdown || {}).length === 0 ? (
                  <div style={{ color: '#6482A6', fontSize: '0.84rem' }}>No categorized vulnerabilities detected.</div>
                ) : (
                  Object.entries(summary.category_breakdown).map(([cat, count]) => (
                    <div 
                      key={cat}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        padding: '10px 14px', 
                        background: '#040F1E',
                        borderRadius: '8px',
                        border: '1px solid #0F2F4E',
                        fontSize: '0.86rem' 
                      }}
                    >
                      <span style={{ color: '#FFFFFF', fontWeight: 500 }}>
                        {cat === 'BOLA' && 'API1:2023 Broken Object Level Authorization (BOLA)'}
                        {cat === 'AUTH' && 'API2:2023 Broken Authentication & Token Handling'}
                        {cat === 'HEADERS' && 'API8:2023 Security Misconfiguration (Headers)'}
                        {cat === 'CONFIG' && 'API8:2023 Information Disclosure & Config'}
                        {!['BOLA', 'AUTH', 'HEADERS', 'CONFIG'].includes(cat) && `OWASP Category: ${cat}`}
                      </span>
                      <span 
                        style={{ 
                          color: cat === 'BOLA' ? '#FF4D5E' : '#00E5FF', 
                          fontWeight: 700, 
                          fontFamily: 'JetBrains Mono, monospace' 
                        }}
                      >
                        {count} {count === 1 ? 'Finding' : 'Findings'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Severity Breakdown */}
            <div className="cyber-card" style={{ padding: '24px' }}>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '16px' }}>
                Severity Distribution
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { label: 'Critical', color: '#FF4D5E', key: 'Critical' },
                  { label: 'High', color: '#FF8A1F', key: 'High' },
                  { label: 'Medium', color: '#FFD21F', key: 'Medium' },
                  { label: 'Low', color: '#00E5FF', key: 'Low' },
                  { label: 'Informational', color: '#8AA4C8', key: 'Informational' },
                ].map((s) => {
                  const count = summary.severity_breakdown?.[s.key] || 0;
                  return (
                    <div 
                      key={s.key}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        padding: '8px 12px',
                        borderBottom: '1px solid rgba(15, 47, 78, 0.4)',
                        fontSize: '0.86rem' 
                      }}
                    >
                      <span style={{ color: s.color, fontWeight: 600 }}>{s.label}</span>
                      <span className="font-mono-code" style={{ color: count > 0 ? '#FFFFFF' : '#54718C', fontWeight: 700 }}>
                        {count}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function Reports(props) {
  return (
    <ErrorBoundary title="Reports Module Intercepted">
      <ReportsContent {...props} />
    </ErrorBoundary>
  );
}
