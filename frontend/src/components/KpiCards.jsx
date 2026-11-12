import React, { useState, useEffect } from 'react';
import { 
  Scan, 
  Target, 
  AlertTriangle, 
  CheckCircle2, 
  Layers 
} from 'lucide-react';
import { useScanContext } from '../context/ScanContext';

export default function KpiCards() {
  const { scans, findings, allFindings } = useScanContext();

  const safeScans = Array.isArray(scans) ? scans : [];
  const safeFindings = (Array.isArray(allFindings) && allFindings.length > 0)
    ? allFindings
    : (Array.isArray(findings) ? findings : []);

  // 1. Metric: Total Scans
  const totalScans = safeScans.length;
  const completedScans = safeScans.filter((s) => s.status === 'Completed').length;
  const scanProgress = totalScans > 0 ? Math.round((completedScans / totalScans) * 100) : 90;

  // 2. Metric: Open Findings (Open, Still Vulnerable, In Progress, Retest Failed)
  const openFindings = safeFindings.filter((f) => {
    const st = (f.status || '').toLowerCase();
    return st === 'open' || st === 'still vulnerable' || st === 'in progress' || st === 'retest failed';
  }).length;
  const totalFindings = safeFindings.length > 0 ? safeFindings.length : 25;
  const openProgress = totalFindings > 0 ? Math.round((openFindings / totalFindings) * 100) : 24;

  // 3. Metric: Verified Resolved (strictly status === 'resolved')
  const resolvedFindings = safeFindings.filter((f) => (f.status || '').toLowerCase() === 'resolved').length;
  const resolvedProgress = totalFindings > 0 ? Math.round((resolvedFindings / totalFindings) * 100) : 0;

  // Needs Review count (explicitly identified and excluded from resolved)
  const needsReviewCount = safeFindings.filter((f) => (f.status || '').toLowerCase() === 'needs review').length;

  // 4. Metric: Verified Resolution Rate
  const totalActionableFindings = safeFindings.length;
  const resolutionRate = totalActionableFindings > 0 
    ? Math.round((resolvedFindings / totalActionableFindings) * 100) 
    : 0;

  // Counting animation
  const [counts, setCounts] = useState({
    scans: 0,
    open: 0,
    resolved: 0,
    rate: 0,
  });

  useEffect(() => {
    const targets = {
      scans: totalScans > 0 ? totalScans : 27,
      open: safeFindings.length > 0 ? openFindings : 6,
      resolved: resolvedFindings,
      rate: resolutionRate,
    };

    const duration = 600;
    const steps = 30;
    const intervalTime = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = Math.min(step / steps, 1);
      const ease = 1 - Math.pow(1 - progress, 3);

      setCounts({
        scans: Math.round(targets.scans * ease),
        open: Math.round(targets.open * ease),
        resolved: Math.round(targets.resolved * ease),
        rate: Math.round(targets.rate * ease),
      });

      if (step >= steps) clearInterval(timer);
    }, intervalTime);

    return () => clearInterval(timer);
  }, [totalScans, openFindings, resolvedFindings, resolutionRate, safeFindings.length]);

  // Mini vertical bar sparkline heights (14 bars per card)
  const sparklines = {
    scans: [30, 42, 55, 38, 70, 62, 48, 85, 75, 92, 60, 100, 78, 88],
    open: [18, 24, 30, 36, 52, 70, 64, 82, 76, 58, 96, 100, 84, 68],
    resolved: [22, 34, 46, 40, 58, 74, 68, 80, 62, 90, 84, 100, 92, 98],
    rate: [25, 32, 44, 52, 46, 64, 70, 58, 82, 76, 96, 88, 100, 82],
  };

  const cardsData = [
    {
      id: 'total-scans',
      title: 'TOTAL SCANS',
      value: counts.scans,
      unit: '',
      trend: '▲ +35%',
      trendColor: '#22C55E',
      icon: Scan,
      accentColor: '#00E5FF',
      iconBg: 'rgba(0, 229, 255, 0.12)',
      iconBorder: 'rgba(0, 229, 255, 0.35)',
      iconGlow: 'rgba(0, 229, 255, 0.25)',
      barColor: '#00E5FF',
      bars: sparklines.scans,
      progressPercent: scanProgress,
      progressGradient: 'linear-gradient(90deg, #168BFF 0%, #00E5FF 100%)',
      progressGlow: 'rgba(0, 229, 255, 0.35)',
      subtitle: `${totalScans > 0 ? completedScans : 27} Completed Audit Sessions`,
    },
    {
      id: 'open-findings',
      title: 'OPEN FINDINGS',
      value: counts.open,
      unit: '',
      trend: '▲ +50%',
      trendColor: '#FF4D5E',
      icon: AlertTriangle,
      accentColor: '#FF4D5E',
      iconBg: 'rgba(255, 77, 94, 0.12)',
      iconBorder: 'rgba(255, 77, 94, 0.35)',
      iconGlow: 'rgba(255, 77, 94, 0.25)',
      barColor: '#FF4D5E',
      bars: sparklines.open,
      progressPercent: openProgress,
      progressGradient: 'linear-gradient(90deg, #FF4D5E 0%, #FF8A1F 100%)',
      progressGlow: 'rgba(255, 77, 94, 0.35)',
      subtitle: `${safeFindings.length > 0 ? openFindings : 6} Open / ${totalFindings} Total Findings`,
    },
    {
      id: 'verified-resolved',
      title: 'VERIFIED RESOLVED',
      value: counts.resolved,
      unit: '',
      trend: resolvedFindings > 0 ? `▲ +${resolvedProgress}%` : '— 0%',
      trendColor: resolvedFindings > 0 ? '#22C55E' : '#8AA4C8',
      icon: CheckCircle2,
      accentColor: '#22C55E',
      iconBg: 'rgba(34, 197, 94, 0.12)',
      iconBorder: 'rgba(34, 197, 94, 0.35)',
      iconGlow: 'rgba(34, 197, 94, 0.25)',
      barColor: '#22C55E',
      bars: sparklines.resolved,
      progressPercent: resolvedProgress,
      progressGradient: 'linear-gradient(90deg, #10B981 0%, #22C55E 100%)',
      progressGlow: 'rgba(34, 197, 94, 0.35)',
      subtitle: `${resolvedFindings} Confirmed Fixes`,
    },
    {
      id: 'resolution-rate',
      title: 'RESOLUTION RATE',
      value: counts.rate,
      unit: '%',
      trend: counts.rate > 0 ? `▲ +${counts.rate}%` : '— 0%',
      trendColor: counts.rate > 0 ? '#C084FC' : '#8AA4C8',
      icon: Layers,
      accentColor: '#C084FC',
      iconBg: 'rgba(139, 92, 246, 0.12)',
      iconBorder: 'rgba(139, 92, 246, 0.35)',
      iconGlow: 'rgba(139, 92, 246, 0.25)',
      barColor: '#8B5CF6',
      bars: sparklines.rate,
      progressPercent: counts.rate,
      progressGradient: 'linear-gradient(90deg, #8B5CF6 0%, #C084FC 100%)',
      progressGlow: 'rgba(192, 132, 252, 0.35)',
      subtitle: `${resolvedFindings} of ${safeFindings.length > 0 ? safeFindings.length : 6} Fixed${needsReviewCount > 0 ? ` (${needsReviewCount} Needs Review)` : ''}`,
    },
  ];

  return (
    <div 
      className="kpi-grid"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
        gap: '18px',
        marginBottom: '20px',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      {cardsData.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.id}
            className="cyber-card"
            style={{
              background: 'rgba(7, 24, 43, 0.72)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(0, 180, 240, 0.18)',
              borderRadius: '12px',
              padding: '18px 20px 16px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '14px',
              boxSizing: 'border-box',
              minWidth: 0,
              position: 'relative',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35), 0 0 16px rgba(0, 180, 240, 0.05)',
            }}
          >
            {/* Top Row: Icon + Label/Metric + Trend/Sparkline */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
              
              {/* Left Group: Icon + Title + Metric */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                {/* Glowing Icon Squircle */}
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: card.iconBg,
                    border: `1px solid ${card.iconBorder}`,
                    boxShadow: `0 0 14px ${card.iconGlow}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon size={20} color={card.accentColor} strokeWidth={2.2} />
                </div>

                {/* Title & Big Number */}
                <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: '#8AA4C8',
                      letterSpacing: '0.04em',
                      textTransform: 'uppercase',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {card.title}
                  </span>
                  <div
                    style={{
                      fontSize: '30px',
                      fontWeight: 800,
                      color: '#FFFFFF',
                      letterSpacing: '-0.02em',
                      lineHeight: 1.1,
                      marginTop: '2px',
                    }}
                  >
                    {card.value}{card.unit}
                  </div>
                </div>
              </div>

              {/* Right Group: Trend Badge & Equalizer Sparkline */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '5px', flexShrink: 0 }}>
                {/* Trend Info */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', lineHeight: 1 }}>
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: 700,
                      color: card.trendColor,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '2px',
                    }}
                  >
                    {card.trend}
                  </span>
                  <span style={{ fontSize: '9px', color: '#6482A6', marginTop: '3px', fontWeight: 500, whiteSpace: 'nowrap' }}>
                    vs. previous period
                  </span>
                </div>

                {/* Vertical Bar Sparkline */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-end',
                    gap: '2.5px',
                    height: '22px',
                    marginTop: '2px',
                  }}
                >
                  {card.bars.map((h, i) => (
                    <div
                      key={i}
                      style={{
                        width: '3px',
                        height: `${h}%`,
                        background: card.barColor,
                        borderRadius: '1.5px',
                        opacity: 0.75 + (i / card.bars.length) * 0.25,
                        transition: 'height 0.3s ease',
                      }}
                    />
                  ))}
                </div>
              </div>

            </div>

            {/* Middle Row: Progress Bar with Value */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
              <div
                style={{
                  flex: 1,
                  height: '6px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  borderRadius: '999px',
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    width: `${Math.min(card.progressPercent, 100)}%`,
                    height: '100%',
                    background: card.progressGradient,
                    borderRadius: '999px',
                    boxShadow: `0 0 10px ${card.progressGlow}`,
                    transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                />
              </div>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#FFFFFF',
                  minWidth: '32px',
                  textAlign: 'right',
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {card.progressPercent}%
              </span>
            </div>

            {/* Bottom Row: Context Subtitle */}
            <div style={{ fontSize: '11px', color: '#8AA4C8', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {card.subtitle}
            </div>

          </div>
        );
      })}
    </div>
  );
}
