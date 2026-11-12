import React, { useState, useMemo } from 'react';
import { useScanContext } from '../context/ScanContext';
import { Activity, Play, RefreshCw } from 'lucide-react';

export default function ScanActivityChart({ onTriggerScan }) {
  const { scans, isLoadingScans } = useScanContext();
  const [hoveredPoint, setHoveredPoint] = useState(null);

  // Group real scans into rolling 14-day calendar window
  const chartData = useMemo(() => {
    const safeScans = Array.isArray(scans) ? scans : [];
    
    // Build 14 calendar day slots ending today
    const days = [];
    const now = new Date();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      days.push(d);
    }

    // Map and count scans matching each calendar day
    const aggregated = days.map((day) => {
      const year = day.getFullYear();
      const month = day.getMonth();
      const date = day.getDate();

      const matchingScans = safeScans.filter((s) => {
        if (!s.created_at) return false;
        const sDate = new Date(s.created_at);
        return (
          sDate.getFullYear() === year &&
          sDate.getMonth() === month &&
          sDate.getDate() === date
        );
      });

      const label = day.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
      return {
        date: label,
        fullDate: day.toISOString().split('T')[0],
        count: matchingScans.length,
      };
    });

    const counts = aggregated.map((d) => d.count);
    const maxCount = Math.max(...counts, 0);

    return {
      points: aggregated,
      totalScansInWindow: counts.reduce((a, b) => a + b, 0),
      maxVal: maxCount <= 5 ? 5 : (maxCount <= 10 ? 10 : Math.ceil(maxCount / 5) * 5),
    };
  }, [scans]);

  const { points: dataPoints, maxVal, totalScansInWindow } = chartData;

  // SVG viewBox geometry calibrated for 1600x900 viewport
  const width = 680;
  const height = 200;
  const padLeft = 32;
  const padRight = 20;
  const padTop = 18;
  const padBottom = 28;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const svgPoints = dataPoints.map((pt, idx) => {
    const x = padLeft + (idx / (dataPoints.length - 1)) * chartW;
    const y = padTop + (1 - pt.count / maxVal) * chartH;
    return { ...pt, x, y, idx };
  });

  // Smooth spline curve
  const createSpline = (pts, tension = 0.3) => {
    if (pts.length < 2) return '';
    let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const pPrev = i > 0 ? pts[i - 1] : pts[i];
      const pCur = pts[i];
      const pNext = pts[i + 1];
      const pNextNext = i < pts.length - 2 ? pts[i + 2] : pNext;

      const cp1x = pCur.x + ((pNext.x - pPrev.x) * tension);
      const cp1y = pCur.y + ((pNext.y - pPrev.y) * tension);
      const cp2x = pNext.x - ((pNextNext.x - pCur.x) * tension);
      const cp2y = pNext.y - ((pNextNext.y - pCur.y) * tension);

      d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${pNext.x.toFixed(1)} ${pNext.y.toFixed(1)}`;
    }
    return d;
  };

  const lineD = createSpline(svgPoints);
  const areaD = `${lineD} L ${svgPoints[svgPoints.length - 1].x.toFixed(1)} ${(padTop + chartH).toFixed(1)} L ${svgPoints[0].x.toFixed(1)} ${(padTop + chartH).toFixed(1)} Z`;

  // Dynamic Y-axis ticks
  const yTicks = maxVal <= 5 ? [0, 1, 2, 3, 4, 5] : [0, 2, 4, 6, 8, 10];

  const hasScans = Array.isArray(scans) && scans.length > 0;

  return (
    <div 
      className="cyber-card"
      style={{
        background: 'rgba(8, 24, 46, 0.70)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(0, 180, 240, 0.18)',
        borderRadius: '14px',
        padding: '24px 26px 20px 26px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35), 0 0 20px rgba(0, 180, 240, 0.06)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="#00E5FF" />
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#FFFFFF', letterSpacing: '-0.01em' }}>
            Scan Activity
          </span>
          <span style={{ fontSize: '13px', fontWeight: 500, color: '#8AA4C8' }}>
            (Last 14 Days)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#FFFFFF', fontWeight: 500 }}>
          <span 
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#00E5FF',
              boxShadow: '0 0 8px #00E5FF',
              display: 'inline-block'
            }}
          />
          <span style={{ color: '#E8F1FF' }}>
            {totalScansInWindow} Scan{totalScansInWindow === 1 ? '' : 's'} Executed
          </span>
        </div>
      </div>

      {/* Main Chart Body */}
      {isLoadingScans ? (
        <div style={{ height: '190px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8AA4C8', gap: '8px' }}>
          <RefreshCw size={18} className="animate-spin" color="#00E5FF" />
          <span style={{ fontSize: '13px' }}>Aggregating scan telemetry from database...</span>
        </div>
      ) : !hasScans ? (
        /* Honest Zero-State Display (Never fabricated values) */
        <div 
          style={{ 
            height: '190px', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            color: '#8AA4C8',
            textAlign: 'center',
            padding: '20px'
          }}
        >
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#E8F1FF', marginBottom: '6px' }}>
            No Historical Scan Activity Recorded
          </div>
          <div style={{ fontSize: '12px', color: '#6482A6', maxWidth: '380px', marginBottom: '12px', lineHeight: '1.4' }}>
            Launch an automated security audit against your target API to populate daily scan volume and historical activity trends.
          </div>
          {onTriggerScan && (
            <button
              onClick={onTriggerScan}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: '6px',
                background: 'rgba(0, 229, 255, 0.15)',
                border: '1px solid #00E5FF',
                color: '#00E5FF',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Play size={12} />
              <span>Launch First Scan</span>
            </button>
          )}
        </div>
      ) : (
        /* Factual SVG Spline Chart */
        <div style={{ position: 'relative', width: '100%', height: '190px' }}>
          <svg 
            viewBox={`0 0 ${width} ${height}`} 
            style={{ width: '100%', height: '100%', overflow: 'visible' }}
            onMouseLeave={() => setHoveredPoint(null)}
          >
            <defs>
              <linearGradient id="realScanAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.28" />
                <stop offset="60%" stopColor="#00E5FF" stopOpacity="0.06" />
                <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.0" />
              </linearGradient>

              <filter id="realCyanLineGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#00E5FF" floodOpacity="0.5" />
              </filter>
            </defs>

            {/* Horizontal Gridlines & Y-Axis Numbers */}
            {yTicks.map((yTick) => {
              const yPos = padTop + (1 - yTick / maxVal) * chartH;
              return (
                <g key={yTick}>
                  <line
                    x1={padLeft}
                    y1={yPos}
                    x2={padLeft + chartW}
                    y2={yPos}
                    stroke="rgba(255, 255, 255, 0.08)"
                    strokeWidth="1"
                  />
                  <text
                    x={padLeft - 8}
                    y={yPos + 4}
                    fill="#7892B0"
                    fontSize="11"
                    fontFamily="'Inter', -apple-system, sans-serif"
                    fontWeight="500"
                    textAnchor="end"
                  >
                    {yTick}
                  </text>
                </g>
              );
            })}

            {/* X-Axis Dates */}
            {svgPoints.map((pt, i) => (
              <text
                key={i}
                x={pt.x}
                y={padTop + chartH + 19}
                fill={hoveredPoint === i ? '#00E5FF' : '#7892B0'}
                fontSize="10"
                fontFamily="'Inter', -apple-system, sans-serif"
                fontWeight={hoveredPoint === i ? '700' : '500'}
                textAnchor="middle"
              >
                {pt.date}
              </text>
            ))}

            {/* Radiant Area Fill */}
            <path d={areaD} fill="url(#realScanAreaGrad)" />

            {/* Spline Path */}
            <path
              d={lineD}
              fill="none"
              stroke="#00E5FF"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#realCyanLineGlow)"
            />

            {/* Interactive Data Points */}
            {svgPoints.map((pt, i) => (
              <g key={i}>
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={hoveredPoint === i ? '6' : (pt.count > 0 ? '4' : '2.5')}
                  fill={hoveredPoint === i ? '#00E5FF' : (pt.count > 0 ? '#00E5FF' : '#1A3A5A')}
                  stroke={hoveredPoint === i ? '#FFFFFF' : '#04101F'}
                  strokeWidth="2"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={() => setHoveredPoint(i)}
                />
              </g>
            ))}
          </svg>

          {/* Tooltip on Hover */}
          {hoveredPoint !== null && (
            <div
              style={{
                position: 'absolute',
                left: `${(svgPoints[hoveredPoint].x / width) * 100}%`,
                top: `${Math.max(8, (svgPoints[hoveredPoint].y / height) * 100 - 35)}%`,
                transform: 'translate(-50%, -100%)',
                background: '#041224',
                border: '1px solid #00E5FF',
                borderRadius: '6px',
                padding: '5px 10px',
                fontSize: '11px',
                color: '#FFFFFF',
                boxShadow: '0 4px 14px rgba(0, 0, 0, 0.7), 0 0 10px rgba(0, 229, 255, 0.3)',
                pointerEvents: 'none',
                whiteSpace: 'nowrap',
                zIndex: 20,
              }}
            >
              <div style={{ color: '#00E5FF', fontWeight: 700 }}>
                {svgPoints[hoveredPoint].date} ({svgPoints[hoveredPoint].fullDate})
              </div>
              <div>
                <strong>{svgPoints[hoveredPoint].count}</strong> scan{svgPoints[hoveredPoint].count === 1 ? '' : 's'} recorded
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
