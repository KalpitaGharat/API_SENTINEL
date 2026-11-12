import React, { useState } from 'react';
import { 
  FileText, 
  Globe, 
  Layers, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Play,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';

export default function LastScanSummary({ onTriggerScan }) {
  const { activeScan, scans, selectedScanId, selectScan } = useScanContext();

  const currentScan = activeScan || (scans && scans.length > 0 ? scans[0] : null);

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={18} color="#00E5FF" strokeWidth={2.2} />
            <span style={{ fontSize: '15px', fontWeight: 700, color: '#E8F1FF' }}>
              Active Scan Session
            </span>
          </div>

          {currentScan && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: currentScan.status === 'Completed' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 138, 31, 0.15)',
                color: currentScan.status === 'Completed' ? '#22C55E' : '#FF8A1F',
                border: `1px solid ${currentScan.status === 'Completed' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255, 138, 31, 0.4)'}`,
              }}
            >
              {currentScan.status === 'Completed' ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
              <span>{currentScan.status?.toUpperCase()}</span>
            </span>
          )}
        </div>

        {!currentScan ? (
          <div style={{ padding: '24px 10px', textAlign: 'center', color: '#6482A6', fontSize: '13px' }}>
            No scan sessions available in database. Launch a security audit from the New Scan tab.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
            <div>
              <span style={{ color: '#8AA4C8', fontSize: '11px', textTransform: 'uppercase' }}>Target URL</span>
              <div className="font-mono-code" style={{ color: '#00E5FF', fontWeight: 600, marginTop: '2px', wordBreak: 'break-all' }}>
                {currentScan.target_url}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <span style={{ color: '#8AA4C8', fontSize: '11px', textTransform: 'uppercase' }}>Scan ID</span>
                <div className="font-mono-code" style={{ color: '#FFFFFF', marginTop: '2px' }}>
                  {currentScan.id?.substring(0, 8)}...
                </div>
              </div>
              <div>
                <span style={{ color: '#8AA4C8', fontSize: '11px', textTransform: 'uppercase' }}>Findings Detected</span>
                <div style={{ color: '#FF4D5E', fontWeight: 700, marginTop: '2px' }}>
                  {currentScan.total_findings} Vulnerabilities
                </div>
              </div>
            </div>

            <div>
              <span style={{ color: '#8AA4C8', fontSize: '11px', textTransform: 'uppercase' }}>Audited At</span>
              <div style={{ color: '#8AA4C8', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={13} color="#6482A6" />
                <span>{new Date(currentScan.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '20px', paddingTop: '14px', borderTop: '1px solid rgba(15, 47, 78, 0.6)' }}>
        <button
          onClick={onTriggerScan}
          style={{
            width: '100%',
            padding: '10px',
            background: 'rgba(0, 229, 255, 0.12)',
            border: '1px solid rgba(0, 229, 255, 0.35)',
            borderRadius: '6px',
            color: '#00E5FF',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            transition: 'all 0.2s ease',
          }}
        >
          <Play size={14} fill="#00E5FF" />
          <span>Launch New Scan Against Target</span>
        </button>
      </div>
    </div>
  );
}
