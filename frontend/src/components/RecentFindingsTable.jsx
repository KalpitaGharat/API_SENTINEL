import React, { useState } from 'react';
import { useScanContext } from '../context/ScanContext';
import { ArrowRight, ShieldCheck, Sparkles, Clock, AlertTriangle } from 'lucide-react';

export default function RecentFindingsTable({ onViewAll, onInspectFinding }) {
  const { findings, selectScan } = useScanContext();
  const [hoveredRow, setHoveredRow] = useState(null);

  const getSeverityBadge = (sev) => {
    const s = (sev || '').toLowerCase();
    if (s === 'critical') return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E', border: 'rgba(255, 77, 94, 0.4)' };
    if (s === 'high') return { bg: 'rgba(255, 138, 31, 0.15)', text: '#FF8A1F', border: 'rgba(255, 138, 31, 0.4)' };
    if (s === 'medium') return { bg: 'rgba(255, 210, 31, 0.15)', text: '#FFD21F', border: 'rgba(255, 210, 31, 0.4)' };
    return { bg: 'rgba(0, 229, 255, 0.15)', text: '#00E5FF', border: 'rgba(0, 229, 255, 0.4)' };
  };

  const getStatusBadge = (status) => {
    const st = (status || '').toLowerCase();
    if (st === 'resolved') {
      return { bg: 'rgba(34, 197, 94, 0.15)', text: '#22C55E', border: 'rgba(34, 197, 94, 0.4)', label: 'RESOLVED' };
    }
    if (st === 'still vulnerable') {
      return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E', border: 'rgba(255, 77, 94, 0.4)', label: 'STILL VULNERABLE' };
    }
    if (st === 'needs review') {
      return { bg: 'rgba(255, 210, 31, 0.15)', text: '#FFD21F', border: 'rgba(255, 210, 31, 0.4)', label: 'NEEDS REVIEW' };
    }
    return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E', border: 'rgba(255, 77, 94, 0.4)', label: 'OPEN' };
  };

  const safeFindings = Array.isArray(findings) ? findings : [];
  const displayList = safeFindings.slice(0, 6);

  const handleRowClick = (finding) => {
    if (finding.scan_id) {
      selectScan(finding.scan_id);
    }
    if (onInspectFinding) {
      onInspectFinding(finding);
    } else if (onViewAll) {
      onViewAll();
    }
  };

  return (
    <div 
      className="cyber-card"
      style={{
        padding: '22px 24px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative'
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#00E5FF" />
            <span style={{ fontSize: '15px', fontWeight: 700, color: '#E8F1FF' }}>
              Recent Vulnerability Findings
            </span>
          </div>

          {onViewAll && (
            <button
              onClick={onViewAll}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: 'transparent',
                border: 'none',
                color: '#00E5FF',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <span>View All ({safeFindings.length})</span>
              <ArrowRight size={13} />
            </button>
          )}
        </div>

        {displayList.length === 0 ? (
          <div style={{ padding: '36px 20px', textAlign: 'center', color: '#6482A6', fontSize: '13px' }}>
            <ShieldCheck size={28} color="#22C55E" style={{ margin: '0 auto 8px auto', opacity: 0.8 }} />
            <div style={{ color: '#FFFFFF', fontWeight: 600, marginBottom: '4px' }}>
              No Vulnerability Findings Detected
            </div>
            <div>
              Target API is currently conforming to audited security baselines.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0F2F4E', color: '#8AA4C8', textAlign: 'left' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Vulnerability Type</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Affected Endpoint</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Severity</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Detected At</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {displayList.map((f, idx) => {
                  const sev = getSeverityBadge(f.severity);
                  const stat = getStatusBadge(f.status);

                  return (
                    <tr 
                      key={f.id || idx}
                      onMouseEnter={() => setHoveredRow(f.id)}
                      onMouseLeave={() => setHoveredRow(null)}
                      onClick={() => handleRowClick(f)}
                      style={{
                        borderBottom: '1px solid rgba(15, 47, 78, 0.4)',
                        background: hoveredRow === f.id ? 'rgba(0, 229, 255, 0.05)' : 'transparent',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <td style={{ padding: '10px', color: '#FFFFFF', fontWeight: 600, maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.vulnerability}
                      </td>
                      <td className="font-mono-code" style={{ padding: '10px', color: '#00E5FF', maxWidth: '170px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.endpoint}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span 
                          style={{
                            display: 'inline-block',
                            padding: '2px 7px',
                            borderRadius: '4px',
                            fontSize: '10.5px',
                            fontWeight: 700,
                            backgroundColor: sev.bg,
                            color: sev.text,
                            border: `1px solid ${sev.border}`,
                          }}
                        >
                          {f.severity?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span 
                          style={{
                            display: 'inline-block',
                            padding: '2px 7px',
                            borderRadius: '4px',
                            fontSize: '10.5px',
                            fontWeight: 700,
                            backgroundColor: stat.bg,
                            color: stat.text,
                            border: `1px solid ${stat.border}`,
                          }}
                        >
                          {stat.label}
                        </span>
                      </td>
                      <td style={{ padding: '10px', color: '#8AA4C8', whiteSpace: 'nowrap' }}>
                        {f.created_at ? new Date(f.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRowClick(f);
                          }}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: 'rgba(0, 229, 255, 0.12)',
                            border: '1px solid rgba(0, 229, 255, 0.35)',
                            color: '#00E5FF',
                            fontSize: '11px',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          <span>Inspect</span>
                          <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
