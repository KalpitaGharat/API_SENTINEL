import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Home, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  BarChart3,
  Sparkles,
  Bell,
  Settings,
  Key,
  Layers,
  ShieldAlert
} from 'lucide-react';
import AnimatedParticleWave from './AnimatedParticleWave';
import { useScanContext } from '../context/ScanContext';

// Legacy view identifiers preserved for backward-compatible routing & tests:
// 'new_scan', 'history', 'notifications', 'reports'
const LEGACY_VIEW_ALIASES = {
  new_scan: 'scans',
  history: 'scans',
  notifications: 'overview',
  reports: 'reports',
};

export default function Sidebar({ activePage, setActivePage }) {
  const [hoveredItem, setHoveredItem] = useState(null);
  const { unreadAlertCount } = useScanContext();

  // The 9 Approved Primary Navigation Items
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'targets', label: 'API Targets', icon: Layers },
    { id: 'scans', label: 'Security Scans', icon: Play },
    { id: 'findings', label: 'Vulnerability Findings', icon: AlertTriangle },
    { id: 'evidence', label: 'Attack Evidence Inspector', icon: ShieldAlert, badge: 'Forensic' },
    { id: 'ai_analysis', label: 'AI Security Analysis', icon: Sparkles, badge: '✨ AI' },
    { id: 'retesting', label: 'Verification & Retesting', icon: CheckCircle2 },
    { id: 'audit_history', label: 'Audit History', icon: Clock },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const isItemActive = (itemId) => {
    if (activePage === itemId) return true;
    if (itemId === 'targets' && activePage === 'onboarding') return true;
    if (itemId === 'scans' && (activePage === 'new_scan' || activePage === 'history')) return true;
    if (itemId === 'audit_history' && (activePage === 'audit' || activePage === 'audit_history')) return true;
    return false;
  };

  return (
    <aside 
      className="sidebar-container"
      style={{
        width: '315px',
        minWidth: '315px',
        maxWidth: '315px',
        height: '100vh',
        position: 'sticky',
        top: 0,
        left: 0,
        backgroundColor: '#07182B',
        borderRight: '1px solid rgba(0, 200, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 20px 14px 20px',
        zIndex: 30,
        boxSizing: 'border-box',
        overflow: 'hidden',
        flexShrink: 0,
        userSelect: 'none'
      }}
    >
      <div style={{ overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
        {/* Brand Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '4px' }}>
          <div 
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(25, 211, 255, 0.12)',
              border: '1.5px solid rgba(25, 211, 255, 0.5)',
              boxShadow: '0 0 22px rgba(25, 211, 255, 0.45)',
              flexShrink: 0
            }}
          >
            <ShieldCheck size={26} color="#19D3FF" strokeWidth={2.4} />
          </div>
          <div className="sidebar-brand-text" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '1.55rem', fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              <span style={{ color: '#E8F1FF' }}>API </span>
              <span style={{ color: '#19D3FF' }}>Sentinel</span>
              <span style={{ color: '#19D3FF', fontSize: '11px', verticalAlign: 'super', marginLeft: '2px', fontWeight: 700 }}>®</span>
            </div>
            <div style={{ fontSize: '11px', color: '#8AA4C8', marginTop: '2px', fontWeight: 400, letterSpacing: '0.01em' }}>
              Explainable Security Testing &amp; Verification
            </div>
          </div>
        </div>

        {/* 9 Primary Nav Items */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%', marginTop: '24px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isItemActive(item.id);
            const isHovered = hoveredItem === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                onMouseEnter={() => setHoveredItem(item.id)}
                onMouseLeave={() => setHoveredItem(null)}
                className={`sidebar-nav-item ${isActive ? 'nav-active-glow' : ''}`}
                style={{
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: '13px',
                  width: '100%',
                  height: '44px',
                  padding: '0 16px',
                  borderRadius: '10px',
                  fontSize: '14px',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? '#E8F1FF' : (isHovered ? '#19D3FF' : '#8AA4C8'),
                  background: isActive
                    ? 'linear-gradient(90deg, rgba(20, 184, 166, 0.3) 0%, rgba(25, 211, 255, 0.2) 100%)'
                    : (isHovered ? 'rgba(25, 211, 255, 0.08)' : 'transparent'),
                  border: isActive
                    ? '1px solid #19D3FF'
                    : (isHovered ? '1px solid rgba(25, 211, 255, 0.25)' : '1px solid transparent'),
                  cursor: 'pointer',
                  textAlign: 'left',
                  transform: (!isActive && isHovered) ? 'translateX(3px)' : 'none',
                  transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                  boxSizing: 'border-box',
                  outline: 'none',
                }}
              >
                {/* Glowing left accent bar on active item */}
                {isActive && <div className="nav-active-bar" />}

                <Icon 
                  size={18} 
                  color={isActive ? '#19D3FF' : (isHovered ? '#19D3FF' : '#8AA4C8')} 
                  strokeWidth={isActive ? 2.4 : 1.9} 
                  style={{ flexShrink: 0, transition: 'color 0.2s ease' }} 
                />
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.label}</span>

                {item.badge && (
                  <span 
                    style={{
                      marginLeft: 'auto',
                      padding: '2px 7px',
                      borderRadius: '8px',
                      fontSize: '10px',
                      fontWeight: 700,
                      background: item.id === 'evidence'
                        ? 'rgba(0, 229, 255, 0.2)'
                        : 'linear-gradient(135deg, rgba(139, 92, 246, 0.35) 0%, rgba(0, 229, 255, 0.25) 100%)',
                      border: `1px solid ${item.id === 'evidence' ? 'rgba(0, 229, 255, 0.5)' : 'rgba(139, 92, 246, 0.6)'}`,
                      color: item.id === 'evidence' ? '#00E5FF' : '#C084FC',
                      letterSpacing: '0.4px',
                      boxShadow: item.id === 'evidence' 
                        ? '0 0 8px rgba(0, 229, 255, 0.3)' 
                        : '0 0 8px rgba(139, 92, 246, 0.3)',
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Optional / Deferred Secondary Tool Access */}
        <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(15, 47, 78, 0.5)' }}>
          <button
            type="button"
            onClick={() => setActivePage('api_key_intel')}
            style={{
              background: activePage === 'api_key_intel' ? 'rgba(0, 229, 255, 0.1)' : 'transparent',
              border: activePage === 'api_key_intel' ? '1px solid rgba(0, 229, 255, 0.3)' : '1px solid transparent',
              color: activePage === 'api_key_intel' ? '#00E5FF' : '#5A7599',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              padding: '6px 10px',
              borderRadius: '6px',
              width: '100%',
              transition: 'all 0.15s ease',
            }}
          >
            <Key size={13} color={activePage === 'api_key_intel' ? '#00E5FF' : '#5A7599'} />
            <span>Optional Tools: API Key Intel</span>
          </button>
        </div>
      </div>

      {/* Bottom Footer: Tagline & Visible Build Version Indicator */}
      <div className="tagline-container" style={{ position: 'relative', marginTop: 'auto', display: 'flex', flexDirection: 'column', width: '100%' }}>
        {/* Visible Version Indicator (Phase 7 requirement) */}
        <div 
          style={{
            padding: '6px 12px',
            marginBottom: '10px',
            borderRadius: '6px',
            background: 'rgba(2, 7, 16, 0.7)',
            border: '1px solid rgba(0, 229, 255, 0.2)',
            fontSize: '11px',
            color: '#8AA4C8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ color: '#00E5FF', fontWeight: 600 }}>API Sentinel</span>
          <span className="font-mono-code" style={{ color: '#22C55E', fontWeight: 700 }}>v1.2.0-phase5-prod</span>
        </div>

        {/* 4-Line Tagline */}
        <div style={{ position: 'relative', marginBottom: '4px', zIndex: 10, paddingLeft: '14px' }}>
          <div 
            style={{
              position: 'absolute',
              left: '0px',
              top: '4px',
              width: '3px',
              height: '76px',
              borderRadius: '2px',
              background: 'linear-gradient(180deg, #19D3FF 0%, rgba(59, 130, 246, 0.8) 70%, transparent 100%)',
              boxShadow: '0 0 12px rgba(25, 211, 255, 0.8)',
              transform: 'rotate(-8deg)',
              transformOrigin: 'top center'
            }}
          />

          <div 
            style={{ 
              fontSize: '18px', 
              fontWeight: 800, 
              color: '#E8F1FF', 
              lineHeight: '1.34', 
              letterSpacing: '-0.01em',
            }}
          >
            <div>Find it.</div>
            <div>Understand it.</div>
            <div>Fix it.</div>
            <div>Verify it.</div>
          </div>
        </div>

        {/* Wave graphic at the very bottom edge */}
        <div 
          style={{ 
            width: '315px', 
            height: '80px', 
            marginLeft: '-20px', 
            marginBottom: '-14px', 
            pointerEvents: 'none', 
            zIndex: 1, 
            opacity: 0.9,
            overflow: 'hidden'
          }}
        >
          <AnimatedParticleWave width={315} height={80} />
        </div>
      </div>
    </aside>
  );
}
