import React, { useState } from 'react';
import { useScanContext } from '../context/ScanContext';
import { ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export default function RecentFindingsTable({ onViewAll }) {
  const { findings } = useScanContext();
  const [hoveredRow, setHoveredRow] = useState(null);

  const getSeverityBadge = (sev) => {
    const s = (sev || '').toLowerCase();
    if (s === 'critical') return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E' };
    if (s === 'high') return { bg: 'rgba(255, 138, 31, 0.15)', text: '#FF8A1F' };
    if (s === 'medium') return { bg: 'rgba(255, 210, 31, 0.15)', text: '#FFD21F' };
    return { bg: 'rgba(0, 229, 255, 0.15)', text: '#00E5FF' };
  };

  const getStatusBadge = (status) => {
    const st = (status || '').toLowerCase();
    if (st === 'resolved') return { bg: 'rgba(34, 197, 94, 0.15)', text: '#22C55E' };
    if (st === 'still vulnerable') return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E' };
    return { bg: 'rgba(255, 77, 94, 0.15)', text: '#FF4D5E' };
  };

  const displayList = (findings || []).slice(0, 6);

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
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#E8F1FF' }}>
            Recent Vulnerability Findings
          </span>
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
              <span>View All</span>
              <ArrowRight size={13} />
            </button>
          )}
        </div>

        {displayList.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', color: '#6482A6', fontSize: '13px' }}>
            No vulnerability findings recorded yet. Launch a security scan to begin.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0F2F4E', color: '#8AA4C8', textAlign: 'left' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Vulnerability</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Endpoint</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Severity</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, textAlign: 'right' }}>AI Analysis</th>
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
                      style={{
                        borderBottom: '1px solid rgba(15, 47, 78, 0.4)',
                        background: hoveredRow === f.id ? 'rgba(0, 229, 255, 0.04)' : 'transparent',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <td style={{ padding: '10px', color: '#FFFFFF', fontWeight: 500, maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.vulnerability}
                      </td>
                      <td className="font-mono-code" style={{ padding: '10px', color: '#00E5FF', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.endpoint}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span 
                          style={{
                            display: 'inline-block',
                            padding: '2px 7px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: sev.bg,
                            color: sev.text,
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
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: stat.bg,
                            color: stat.text,
                          }}
                        >
                          {f.status?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={onViewAll}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '3px 9px',
                            borderRadius: '4px',
                            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(0, 229, 255, 0.15) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.5)',
                            color: '#C084FC',
                            fontSize: '11px',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          <Sparkles size={11} color="#C084FC" />
                          <span>AI Explain</span>
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
