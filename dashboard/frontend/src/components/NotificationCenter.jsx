import React from 'react';
import { 
  Bell, 
  ShieldAlert, 
  CheckCircle2, 
  Info, 
  X, 
  ExternalLink, 
  CheckCheck, 
  Terminal,
  AlertTriangle
} from 'lucide-react';

export default function NotificationCenter({
  isOpen,
  onClose,
  notifications = [],
  onSelectFinding,
  onAcknowledgeAll,
  onAcknowledgeOne,
}) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '20px',
        width: '420px',
        maxHeight: '540px',
        background: 'linear-gradient(135deg, rgba(7, 24, 43, 0.98) 0%, rgba(4, 12, 24, 0.98) 100%)',
        border: '1px solid rgba(0, 229, 255, 0.3)',
        borderRadius: '12px',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(0, 229, 255, 0.15)',
        zIndex: 9998,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        animation: 'slideDown 0.2s ease-out',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 18px',
          borderBottom: '1px solid #0F2F4E',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bell size={18} color="#00E5FF" />
          <span style={{ fontSize: '0.94rem', fontWeight: 700, color: '#FFFFFF' }}>
            Security Telemetry & Alerts
          </span>
          <span
            style={{
              padding: '2px 7px',
              borderRadius: '10px',
              fontSize: '0.72rem',
              fontWeight: 700,
              background: 'rgba(0, 229, 255, 0.15)',
              color: '#00E5FF',
              border: '1px solid rgba(0, 229, 255, 0.3)',
            }}
          >
            {notifications.filter((n) => !n.acknowledged).length} Active
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {notifications.some((n) => !n.acknowledged) && (
            <button
              onClick={onAcknowledgeAll}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: 'transparent',
                border: 'none',
                color: '#8AA4C8',
                fontSize: '0.76rem',
                cursor: 'pointer',
              }}
              title="Acknowledge All Alerts"
            >
              <CheckCheck size={14} />
              <span>Acknowledge All</span>
            </button>
          )}

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8AA4C8',
              cursor: 'pointer',
              padding: '2px',
            }}
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Notification Items List */}
      <div
        style={{
          padding: '12px 14px',
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {notifications.length === 0 ? (
          <div style={{ padding: '36px 20px', textAlign: 'center', color: '#6482A6' }}>
            <CheckCircle2 size={32} color="#00E5FF" style={{ margin: '0 auto 10px auto' }} />
            <div style={{ color: '#E8F1FF', fontSize: '0.9rem', fontWeight: 600, marginBottom: '4px' }}>
              All Clear
            </div>
            <div style={{ fontSize: '0.8rem' }}>
              No active security alerts. Real-time background telemetry is running.
            </div>
          </div>
        ) : (
          notifications.map((item) => {
            const isCrit = (item.severity || '').toLowerCase() === 'critical';
            const isHigh = (item.severity || '').toLowerCase() === 'high';
            const borderColor = isCrit ? '#FF4D5E' : isHigh ? '#FF8A1F' : '#0F2F4E';

            return (
              <div
                key={item.id}
                style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: item.acknowledged ? 'rgba(4, 12, 24, 0.45)' : 'rgba(4, 16, 32, 0.9)',
                  borderLeft: `4px solid ${borderColor}`,
                  borderTop: '1px solid #0F2F4E',
                  borderRight: '1px solid #0F2F4E',
                  borderBottom: '1px solid #0F2F4E',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  opacity: item.acknowledged ? 0.7 : 1,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isCrit ? (
                      <ShieldAlert size={15} color="#FF4D5E" />
                    ) : isHigh ? (
                      <AlertTriangle size={15} color="#FF8A1F" />
                    ) : (
                      <Terminal size={15} color="#00E5FF" />
                    )}
                    <span style={{ fontSize: '0.86rem', fontWeight: 600, color: '#FFFFFF' }}>
                      {item.title || item.vulnerability}
                    </span>
                  </div>

                  <span style={{ fontSize: '0.72rem', color: '#6482A6' }}>
                    {item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now'}
                  </span>
                </div>

                {item.endpoint && (
                  <div className="font-mono-code" style={{ fontSize: '0.78rem', color: '#00E5FF' }}>
                    {item.endpoint}
                  </div>
                )}

                <div style={{ fontSize: '0.8rem', color: '#8AA4C8', lineHeight: '1.4' }}>
                  {item.message || item.description}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
                  {!item.acknowledged && (
                    <button
                      onClick={() => onAcknowledgeOne(item.id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#6482A6',
                        fontSize: '0.74rem',
                        cursor: 'pointer',
                        padding: '2px 6px',
                      }}
                    >
                      Dismiss
                    </button>
                  )}

                  {item.findingId && (
                    <button
                      onClick={() => onSelectFinding(item)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: 'rgba(0, 229, 255, 0.12)',
                        border: '1px solid rgba(0, 229, 255, 0.3)',
                        borderRadius: '4px',
                        color: '#00E5FF',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        padding: '3px 8px',
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
          })
        )}
      </div>
    </div>
  );
}
