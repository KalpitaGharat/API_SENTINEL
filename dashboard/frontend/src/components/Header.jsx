import React, { useState } from 'react';
import { Bell, ChevronDown, Radio, Wifi, WifiOff } from 'lucide-react';
import { useScanContext } from '../context/ScanContext';
import NotificationCenter from './NotificationCenter';

export default function Header({ 
  title = "Security Overview", 
  subtitle = "Real-time view of your API security posture, findings, and scan activity.",
  setActivePage
}) {
  const { 
    unreadAlertCount, 
    notifications, 
    acknowledgeAllAlerts, 
    acknowledgeAlert, 
    selectScan, 
    sseStatus 
  } = useScanContext();

  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  const handleSelectFinding = (notif) => {
    setIsNotificationsOpen(false);
    if (notif.scanId) selectScan(notif.scanId);
    if (notif.id) acknowledgeAlert(notif.id);
    if (setActivePage) setActivePage('findings');
  };

  return (
    <div style={{ marginBottom: '22px', position: 'relative' }}>
      <header 
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          animation: 'bootCascade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards'
        }}
      >
        {/* Left Title - Dynamic from current page */}
        <div>
          <h1 
            style={{
              fontSize: '32px',
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              lineHeight: 1.15,
              margin: 0,
            }}
          >
            {title}
          </h1>
          <p style={{ fontSize: '13.5px', color: '#8AA4C8', marginTop: '5px', fontWeight: 400, margin: 0 }}>
            {subtitle}
          </p>
        </div>

        {/* Right Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Live Telemetry Stream Indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 10px',
              borderRadius: '20px',
              background: sseStatus === 'connected' ? 'rgba(34, 197, 94, 0.12)' : 'rgba(255, 138, 31, 0.12)',
              border: `1px solid ${sseStatus === 'connected' ? 'rgba(34, 197, 94, 0.35)' : 'rgba(255, 138, 31, 0.35)'}`,
              fontSize: '0.74rem',
              fontWeight: 600,
              color: sseStatus === 'connected' ? '#22C55E' : '#FF8A1F',
            }}
            title={sseStatus === 'connected' ? 'Server-Sent Events active: real-time live telemetry connected' : 'Connecting to real-time telemetry stream...'}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: sseStatus === 'connected' ? '#22C55E' : '#FF8A1F',
                boxShadow: sseStatus === 'connected' ? '0 0 8px #22C55E' : 'none',
              }}
            />
            <span>{sseStatus === 'connected' ? 'LIVE STREAM' : 'SYNCING'}</span>
          </div>

          {/* Bell Icon with glowing count badge */}
          <button 
            type="button"
            onClick={() => setIsNotificationsOpen((prev) => !prev)}
            style={{
              position: 'relative',
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: isNotificationsOpen ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
              border: isNotificationsOpen ? '1px solid rgba(0, 229, 255, 0.4)' : '1px solid transparent',
              cursor: 'pointer',
              color: '#E8F1FF',
              outline: 'none',
              padding: 0,
              transition: 'all 0.15s ease',
            }}
            title="Notifications & Alerts"
          >
            <Bell size={21} color="#E8F1FF" strokeWidth={1.8} />
            {unreadAlertCount > 0 ? (
              <span 
                style={{
                  position: 'absolute',
                  top: '-2px',
                  right: '-2px',
                  minWidth: '18px',
                  height: '18px',
                  padding: '0 4px',
                  borderRadius: '9px',
                  backgroundColor: '#FF4D5E',
                  color: '#FFFFFF',
                  fontSize: '10px',
                  fontWeight: 800,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 10px rgba(255, 77, 94, 0.6)',
                }}
              >
                {unreadAlertCount > 9 ? '9+' : unreadAlertCount}
              </span>
            ) : (
              <span 
                style={{
                  position: 'absolute',
                  top: '5px',
                  right: '6px',
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  backgroundColor: '#00E5FF',
                  boxShadow: '0 0 8px #00E5FF'
                }}
              />
            )}
          </button>

          {/* Thin vertical divider */}
          <div style={{ width: '1px', height: '22px', backgroundColor: 'rgba(255, 255, 255, 0.15)' }} />

          {/* Profile Pill */}
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              userSelect: 'none'
            }}
          >
            <div 
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#2563EB',
                color: '#FFFFFF',
                fontSize: '13px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              A
            </div>
            <span style={{ fontSize: '13.5px', fontWeight: 600, color: '#E8F1FF' }}>
              API Sentinel Team
            </span>
            <ChevronDown size={14} color="#8AA4C8" />
          </div>
        </div>
      </header>

      {/* Dropdown Notification Center */}
      <NotificationCenter
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        notifications={notifications}
        onSelectFinding={handleSelectFinding}
        onAcknowledgeAll={acknowledgeAllAlerts}
        onAcknowledgeOne={acknowledgeAlert}
      />
    </div>
  );
}
