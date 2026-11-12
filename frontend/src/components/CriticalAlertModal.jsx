import React from 'react';
import { ShieldAlert, AlertTriangle, X, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function CriticalAlertModal({ alert, onInspect, onAcknowledge }) {
  if (!alert) return null;

  const isCritical = (alert.severity || '').toLowerCase() === 'critical';
  const borderColor = isCritical ? '#FF4D5E' : '#FF8A1F';
  const glowColor = isCritical ? 'rgba(255, 77, 94, 0.45)' : 'rgba(255, 138, 31, 0.45)';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(2, 6, 18, 0.78)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        animation: 'fadeIn 0.25s ease-out',
      }}
    >
      <div
        className="cyber-card"
        style={{
          width: '100%',
          maxWidth: '560px',
          background: 'linear-gradient(135deg, rgba(16, 24, 48, 0.98) 0%, rgba(8, 14, 28, 0.98) 100%)',
          border: `2px solid ${borderColor}`,
          borderRadius: '14px',
          boxShadow: `0 0 35px ${glowColor}, 0 20px 40px rgba(0, 0, 0, 0.8)`,
          padding: '26px 28px',
          position: 'relative',
          overflow: 'hidden',
          animation: 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Top Animated Pulse Line */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: `linear-gradient(90deg, transparent, ${borderColor}, transparent)`,
            animation: 'scanline 2s infinite linear',
          }}
        />

        {/* Header Row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: `${borderColor}22`,
                border: `1.5px solid ${borderColor}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 16px ${glowColor}`,
                flexShrink: 0,
              }}
            >
              <ShieldAlert size={26} color={borderColor} strokeWidth={2.2} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    backgroundColor: `${borderColor}33`,
                    color: borderColor,
                    border: `1px solid ${borderColor}66`,
                    letterSpacing: '0.6px',
                  }}
                >
                  {alert.severity?.toUpperCase() || 'CRITICAL'} ALERT
                </span>
                <span style={{ fontSize: '0.75rem', color: '#8AA4C8' }}>
                  {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Just Now'}
                </span>
              </div>
              <h3 style={{ fontSize: '1.18rem', fontWeight: 800, color: '#FFFFFF', marginTop: '4px', margin: 0, letterSpacing: '-0.01em' }}>
                Security Vulnerability Detected
              </h3>
            </div>
          </div>

          <button
            onClick={onAcknowledge}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8AA4C8',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px',
            }}
            title="Dismiss Alert"
          >
            <X size={20} />
          </button>
        </div>

        {/* Vulnerability Summary Card */}
        <div
          style={{
            background: 'rgba(4, 12, 24, 0.85)',
            border: '1px solid #0F2F4E',
            borderRadius: '10px',
            padding: '16px 18px',
            marginBottom: '18px',
          }}
        >
          <div style={{ fontSize: '1.02rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '6px' }}>
            {alert.vulnerability || alert.title}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="font-mono-code" style={{ color: '#00E5FF', fontSize: '0.84rem' }}>
              {alert.endpoint}
            </span>
            <span style={{ color: '#0F2F4E' }}>•</span>
            <span style={{ color: '#8AA4C8', fontSize: '0.78rem' }}>
              {alert.category || 'API Security'}
            </span>
          </div>
          <p style={{ color: '#A5B8CE', fontSize: '0.86rem', lineHeight: '1.5', margin: 0 }}>
            {alert.description || 'Target API endpoint allows unauthorized access or discloses sensitive application state.'}
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="button"
            onClick={onAcknowledge}
            style={{
              padding: '9px 16px',
              borderRadius: '8px',
              background: 'rgba(15, 47, 78, 0.5)',
              border: '1px solid #0F2F4E',
              color: '#8AA4C8',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            Acknowledge & Dismiss
          </button>

          <button
            type="button"
            onClick={() => onInspect(alert)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 18px',
              borderRadius: '8px',
              background: isCritical
                ? 'linear-gradient(135deg, #FF4D5E 0%, #B91C1C 100%)'
                : 'linear-gradient(135deg, #FF8A1F 0%, #C2410C 100%)',
              border: `1px solid ${borderColor}`,
              color: '#FFFFFF',
              fontSize: '0.84rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: `0 0 16px ${glowColor}`,
              transition: 'all 0.15s ease',
            }}
          >
            <span>Inspect Finding with AI</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
