import React, { useState } from 'react';
import { 
  Bell, 
  ShieldAlert, 
  AlertTriangle, 
  Terminal, 
  CheckCircle2, 
  CheckCheck, 
  ExternalLink, 
  RefreshCw,
  Filter
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import ErrorBoundary from '../components/ErrorBoundary';

function NotificationsViewContent({ setActivePage }) {
  const { 
    notifications, 
    acknowledgeAlert, 
    acknowledgeAllAlerts, 
    selectScan, 
    sseStatus 
  } = useScanContext();

  const [filter, setFilter] = useState('All'); // All, Critical, High, Telemetry

  const filtered = notifications.filter((n) => {
    if (filter === 'All') return true;
    if (filter === 'Critical') return (n.severity || '').toLowerCase() === 'critical';
    if (filter === 'High') return (n.severity || '').toLowerCase() === 'high';
    if (filter === 'Telemetry') return n.type === 'scan_created' || n.type === 'scan_completed' || n.type === 'retest_completed';
    return true;
  });

  const handleInspect = (notif) => {
    if (notif.scanId) selectScan(notif.scanId);
    if (notif.id) acknowledgeAlert(notif.id);
    setActivePage('findings');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Bar */}
      <div 
        className="cyber-card" 
        style={{ 
          padding: '18px 22px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px' 
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Live Security Telemetry & Alert Stream
            </h3>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 8px',
                borderRadius: '12px',
                background: sseStatus === 'connected' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 138, 31, 0.15)',
                color: sseStatus === 'connected' ? '#22C55E' : '#FF8A1F',
                fontSize: '0.74rem',
                fontWeight: 700,
                border: `1px solid ${sseStatus === 'connected' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255, 138, 31, 0.4)'}`,
              }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: sseStatus === 'connected' ? '#22C55E' : '#FF8A1F' }} />
              <span>{sseStatus === 'connected' ? 'SSE STREAM ACTIVE' : 'RECONNECTING'}</span>
            </span>
          </div>
          <p style={{ margin: 0, color: '#8AA4C8', fontSize: '0.84rem' }}>
            Real-time feed of newly detected vulnerabilities, scan events, and verification probe outcomes.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Severity Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
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
            <option value="All">All Events & Alerts</option>
            <option value="Critical">Critical Alerts Only</option>
            <option value="High">High Severity Only</option>
            <option value="Telemetry">Scan Lifecycle Only</option>
          </select>

          {notifications.some((n) => !n.acknowledged) && (
            <button
              onClick={acknowledgeAllAlerts}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                background: 'rgba(0, 229, 255, 0.12)',
                border: '1px solid rgba(0, 229, 255, 0.4)',
                color: '#00E5FF',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <CheckCheck size={14} />
              <span>Acknowledge All</span>
            </button>
          )}
        </div>
      </div>

      {/* Notifications Feed */}
      <div className="cyber-card" style={{ padding: '20px' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '50px 20px', textAlign: 'center', color: '#6482A6' }}>
            <CheckCircle2 size={36} color="#00E5FF" style={{ margin: '0 auto 12px auto' }} />
            <h4 style={{ color: '#FFFFFF', fontSize: '1.05rem', marginBottom: '6px' }}>
              All Security Telemetry Acknowledged
            </h4>
            <p style={{ fontSize: '0.84rem', maxWidth: '420px', margin: '0 auto' }}>
              No pending alerts. Incoming security scan events and vulnerability discoveries will stream here in real time.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filtered.map((item) => {
              const isCrit = (item.severity || '').toLowerCase() === 'critical';
              const isHigh = (item.severity || '').toLowerCase() === 'high';
              const borderColor = isCrit ? '#FF4D5E' : isHigh ? '#FF8A1F' : '#00E5FF';

              return (
                <div
                  key={item.id}
                  style={{
                    padding: '16px 18px',
                    borderRadius: '10px',
                    background: item.acknowledged ? 'rgba(4, 12, 24, 0.4)' : 'rgba(4, 16, 32, 0.85)',
                    borderLeft: `4px solid ${borderColor}`,
                    borderTop: '1px solid #0F2F4E',
                    borderRight: '1px solid #0F2F4E',
                    borderBottom: '1px solid #0F2F4E',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '14px',
                    opacity: item.acknowledged ? 0.75 : 1,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: '280px' }}>
                    <div
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '8px',
                        background: `${borderColor}22`,
                        border: `1px solid ${borderColor}55`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {isCrit ? (
                        <ShieldAlert size={20} color="#FF4D5E" />
                      ) : isHigh ? (
                        <AlertTriangle size={20} color="#FF8A1F" />
                      ) : (
                        <Terminal size={18} color="#00E5FF" />
                      )}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                        <span style={{ fontSize: '0.94rem', fontWeight: 600, color: '#FFFFFF' }}>
                          {item.title || item.vulnerability}
                        </span>
                        <span
                          style={{
                            padding: '2px 7px',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: `${borderColor}22`,
                            color: borderColor,
                          }}
                        >
                          {item.severity?.toUpperCase() || 'INFO'}
                        </span>
                      </div>

                      {item.endpoint && (
                        <div className="font-mono-code" style={{ fontSize: '0.8rem', color: '#00E5FF', marginBottom: '4px' }}>
                          {item.endpoint}
                        </div>
                      )}

                      <div style={{ fontSize: '0.82rem', color: '#8AA4C8' }}>
                        {item.message || item.description}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '0.78rem', color: '#6482A6' }}>
                      {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Now'}
                    </span>

                    {!item.acknowledged && (
                      <button
                        onClick={() => acknowledgeAlert(item.id)}
                        style={{
                          background: 'transparent',
                          border: '1px solid #0F2F4E',
                          borderRadius: '6px',
                          color: '#8AA4C8',
                          fontSize: '0.76rem',
                          padding: '5px 10px',
                          cursor: 'pointer',
                        }}
                      >
                        Dismiss
                      </button>
                    )}

                    {item.findingId && (
                      <button
                        onClick={() => handleInspect(item)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
                          border: '1px solid #00E5FF',
                          color: '#00E5FF',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <span>Inspect Finding</span>
                        <ExternalLink size={12} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function NotificationsView(props) {
  return (
    <ErrorBoundary title="Notifications Module Intercepted">
      <NotificationsViewContent {...props} />
    </ErrorBoundary>
  );
}
