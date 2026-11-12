import React, { useState, useEffect } from 'react';
import { Clock, ShieldAlert, CheckCircle2, AlertTriangle, RefreshCw, ArrowRight, ExternalLink } from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';
import ErrorBoundary from '../components/ErrorBoundary';

function ScanHistoryContent({ setActivePage }) {
  const { scans, selectedScanId, selectScan, refreshScans, isLoadingScans } = useScanContext();
  const [filterStatus, setFilterStatus] = useState('All');

  const filteredScans = (scans || []).filter((s) => {
    if (filterStatus === 'All') return true;
    return (s.status || '').toLowerCase() === filterStatus.toLowerCase();
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Controls */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '16px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px' 
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '4px' }}>
            Historical Scan Registry
          </h3>
          <p style={{ color: '#8AA4C8', fontSize: '0.84rem' }}>
            Complete audit trail of all automated API security scans recorded in SQLite persistence.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              padding: '8px 12px',
              background: '#04101F',
              border: '1px solid #0F2F4E',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '0.84rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="All">All Statuses</option>
            <option value="Completed">Completed</option>
            <option value="Running">Running</option>
            <option value="Failed">Failed</option>
          </select>

          <button
            onClick={refreshScans}
            disabled={isLoadingScans}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: '#07182B',
              border: '1px solid #0F2F4E',
              color: '#8AA4C8',
              borderRadius: '8px',
              padding: '8px 14px',
              fontSize: '0.82rem',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} className={isLoadingScans ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Scans Table */}
      <div className="cyber-card" style={{ padding: '20px' }}>
        {isLoadingScans ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#8AA4C8' }}>
            <RefreshCw size={24} className="animate-spin" color="#00E5FF" style={{ margin: '0 auto 10px auto' }} />
            <div>Loading scans from database...</div>
          </div>
        ) : filteredScans.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#8AA4C8' }}>
            <p style={{ marginBottom: '12px' }}>No scan records found matching the selected filter.</p>
            <button
              onClick={() => setActivePage('new_scan')}
              style={{
                padding: '8px 16px',
                background: '#00E5FF',
                color: '#040813',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.84rem',
                cursor: 'pointer',
              }}
            >
              Launch New Scan
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0F2F4E', color: '#8AA4C8', textAlign: 'left' }}>
                  <th style={{ padding: '12px', fontWeight: 600 }}>Scan ID</th>
                  <th style={{ padding: '12px', fontWeight: 600 }}>Target Destination</th>
                  <th style={{ padding: '12px', fontWeight: 600 }}>Timestamp (UTC)</th>
                  <th style={{ padding: '12px', fontWeight: 600 }}>Findings</th>
                  <th style={{ padding: '12px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredScans.map((scan) => {
                  const isSelected = scan.id === selectedScanId;
                  const isCompleted = scan.status === 'Completed';

                  return (
                    <tr 
                      key={scan.id} 
                      style={{ 
                        borderBottom: '1px solid rgba(15, 47, 78, 0.45)',
                        background: isSelected ? 'rgba(0, 229, 255, 0.04)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '14px 12px', fontFamily: 'JetBrains Mono, monospace', color: isSelected ? '#00E5FF' : '#8AA4C8' }}>
                        {scan.id.substring(0, 8)}...
                      </td>
                      <td style={{ padding: '14px 12px', color: '#FFFFFF', fontWeight: 500 }}>
                        <div className="font-mono-code" style={{ fontSize: '0.84rem' }}>
                          {scan.target_url}
                        </div>
                      </td>
                      <td style={{ padding: '14px 12px', color: '#8AA4C8', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={13} color="#6482A6" />
                          <span>{new Date(scan.created_at).toLocaleString()}</span>
                        </div>
                      </td>
                      <td style={{ padding: '14px 12px' }}>
                        <span 
                          style={{ 
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            backgroundColor: scan.total_findings > 0 ? 'rgba(255, 77, 94, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                            color: scan.total_findings > 0 ? '#FF4D5E' : '#22C55E',
                          }}
                        >
                          {scan.total_findings} Detected
                        </span>
                      </td>
                      <td style={{ padding: '14px 12px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: isCompleted 
                              ? 'rgba(34, 197, 94, 0.15)' 
                              : (scan.status === 'Failed' ? 'rgba(255, 77, 94, 0.15)' : 'rgba(255, 138, 31, 0.15)'),
                            color: isCompleted 
                              ? '#22C55E' 
                              : (scan.status === 'Failed' ? '#FF4D5E' : '#FF8A1F'),
                            border: `1px solid ${isCompleted ? 'rgba(34, 197, 94, 0.3)' : (scan.status === 'Failed' ? 'rgba(255, 77, 94, 0.3)' : 'rgba(255, 138, 31, 0.3)')}`,
                          }}
                        >
                          {isCompleted ? <CheckCircle2 size={12} /> : (scan.status === 'Failed' ? <ShieldAlert size={12} /> : <AlertTriangle size={12} />)}
                          <span>{scan.status?.toUpperCase()}</span>
                        </span>
                      </td>
                      <td style={{ padding: '14px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => {
                              selectScan(scan.id);
                              setActivePage('findings', { scanId: scan.id });
                            }}
                            title="Inspect Findings"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '5px 10px',
                              background: isSelected ? '#00E5FF' : 'rgba(0, 229, 255, 0.12)',
                              color: isSelected ? '#040813' : '#00E5FF',
                              border: '1px solid rgba(0, 229, 255, 0.3)',
                              borderRadius: '6px',
                              fontSize: '0.76rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            <span>Findings</span>
                            <ArrowRight size={11} />
                          </button>

                          {scan.total_findings > 0 && (
                            <>
                              <button
                                onClick={() => {
                                  selectScan(scan.id);
                                  setActivePage('evidence', { scanId: scan.id });
                                }}
                                title="Inspect Attack Evidence"
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  padding: '5px 9px',
                                  background: 'rgba(255, 77, 94, 0.12)',
                                  color: '#FF4D5E',
                                  border: '1px solid rgba(255, 77, 94, 0.3)',
                                  borderRadius: '6px',
                                  fontSize: '0.76rem',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                }}
                              >
                                <span>Evidence</span>
                              </button>
                              <button
                                onClick={() => {
                                  selectScan(scan.id);
                                  setActivePage('retesting', { scanId: scan.id });
                                }}
                                title="Verify & Retest"
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  padding: '5px 9px',
                                  background: 'rgba(34, 197, 94, 0.12)',
                                  color: '#22C55E',
                                  border: '1px solid rgba(34, 197, 94, 0.3)',
                                  borderRadius: '6px',
                                  fontSize: '0.76rem',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                }}
                              >
                                <span>Retest</span>
                              </button>
                            </>
                          )}
                        </div>
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

export default function ScanHistory(props) {
  return (
    <ErrorBoundary title="Scan History Intercepted">
      <ScanHistoryContent {...props} />
    </ErrorBoundary>
  );
}
