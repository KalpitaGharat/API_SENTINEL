import React, { useState } from 'react';

/**
 * KpiCyberGraph - "Crazy Good" Cyber Telemetry Sparkline
 * Features:
 * - Fluid high-precision Catmull-Rom cubic bezier spline
 * - Traveling neon laser energy packet (gliding comet shimmer along the curve)
 * - Dual-layer neon bloom & radiant area glow
 * - Multi-frequency trailing ghost depth path
 * - Concentric radar beacon ping at the latest telemetry tip
 * - Interactive hover with crosshair and glowing node magnification
 */
export default function KpiCyberGraph({ 
  type = 'scans', // 'scans' | 'vulns' | 'fixed'
  color = '#00E5FF',
  glowColor = 'rgba(0, 229, 255, 0.65)',
  height = 46
}) {
  const [hoveredNode, setHoveredNode] = useState(null);

  // Calibrated trend trajectories matching the KPI values:
  const trendData = {
    scans: [13.2, 15.8, 14.2, 18.5, 17.0, 21.4, 24.0],
    vulns: [45.5, 42.8, 44.0, 40.8, 39.2, 38.0, 37.0],
    fixed: [16.0, 18.2, 19.5, 22.0, 23.8, 26.2, 28.0],
  };

  const rawValues = trendData[type] || trendData.scans;
  const minVal = Math.min(...rawValues) * 0.86;
  const maxVal = Math.max(...rawValues) * 1.08;
  const range = maxVal - minVal || 1;

  const width = 240;
  const padX = 10;
  const padTop = 8;
  const padBottom = 8;
  const drawW = width - padX * 2;
  const drawH = height - padTop - padBottom;

  const points = rawValues.map((v, i) => {
    const x = padX + (i / (rawValues.length - 1)) * drawW;
    const y = padTop + (1 - (v - minVal) / range) * drawH;
    return { x, y, val: v, idx: i };
  });

  // Silky smooth natural spline (tension = 0.36)
  const createSpline = (pts, tension = 0.36) => {
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

  const lineD = createSpline(points);
  const areaD = `${lineD} L ${points[points.length - 1].x.toFixed(1)} ${height} L ${points[0].x.toFixed(1)} ${height} Z`;

  // Secondary ghost wave (slight vertical offset for 3D holographic depth)
  const ghostPoints = points.map(p => ({ x: p.x, y: Math.min(height - 4, p.y + 4.5) }));
  const ghostD = createSpline(ghostPoints);

  const gradId = `crazyGrad_${type}`;
  const glowFilterId = `crazyGlow_${type}`;
  const lastPt = points[points.length - 1];

  return (
    <div 
      style={{ 
        width: '100%', 
        height: `${height}px`, 
        position: 'relative', 
        overflow: 'hidden',
        userSelect: 'none'
      }}
      onMouseLeave={() => setHoveredNode(null)}
    >
      <svg 
        viewBox={`0 0 ${width} ${height}`} 
        style={{ width: '100%', height: '100%', overflow: 'visible', display: 'block' }}
      >
        <defs>
          {/* Luminous multi-stop vertical radiant gradient */}
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.38" />
            <stop offset="55%" stopColor={color} stopOpacity="0.10" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>

          {/* Intense neon bloom filter */}
          <filter id={glowFilterId} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.2" result="blur1" />
            <feGaussianBlur stdDeviation="1.5" result="blur2" />
            <feMerge>
              <feMergeNode in="blur1" />
              <feMergeNode in="blur2" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* 1. Luminous Glowing Area Gradient Fill */}
        <path d={areaD} fill={`url(#${gradId})`} />

        {/* 2. Trailing 3D Holographic Ghost Wave */}
        <path 
          d={ghostD} 
          fill="none" 
          stroke={color} 
          strokeWidth="1.2" 
          strokeDasharray="2 3" 
          opacity="0.22" 
        />

        {/* 3. Deep Neon Halo Underglow */}
        <path 
          d={lineD} 
          fill="none" 
          stroke={color} 
          strokeWidth="6" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          opacity="0.28"
          filter={`url(#${glowFilterId})`}
        />

        {/* 4. Sharp High-Precision Main Laser Spline */}
        <path 
          d={lineD} 
          fill="none" 
          stroke={color} 
          strokeWidth="2.4" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          filter={`url(#${glowFilterId})`}
        />

        {/* 5. Traveling Neon Energy Comet Gliding along the line */}
        <path 
          d={lineD} 
          fill="none" 
          stroke="#FFFFFF" 
          strokeWidth="2.6" 
          strokeLinecap="round" 
          strokeDasharray="18 160"
          className="kpi-laser-shimmer"
          opacity="0.95"
        />

        {/* 6. Subtle intermediate data nodes */}
        {points.slice(0, -1).map((pt, i) => {
          const isHovered = hoveredNode === i;
          return (
            <g key={i} onMouseEnter={() => setHoveredNode(i)} style={{ cursor: 'pointer' }}>
              <circle cx={pt.x} cy={pt.y} r="8" fill="transparent" />
              <circle
                cx={pt.x}
                cy={pt.y}
                r={isHovered ? 3.5 : 2}
                fill={isHovered ? '#FFFFFF' : color}
                style={{
                  filter: `drop-shadow(0 0 5px ${color})`,
                  transition: 'all 0.15s ease'
                }}
              />
            </g>
          );
        })}

        {/* 7. Pulsing Concentric Radar Beacon Rings at Latest Tip */}
        {/* Outer Ripple 1 */}
        <circle
          cx={lastPt.x}
          cy={lastPt.y}
          r="4"
          fill="none"
          stroke={color}
          strokeWidth="1.4"
          opacity="0.8"
        >
          <animate attributeName="r" values="3;11;14" dur="2.2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.8;0.2;0" dur="2.2s" repeatCount="indefinite" />
        </circle>

        {/* Outer Ripple 2 (staggered) */}
        <circle
          cx={lastPt.x}
          cy={lastPt.y}
          r="3"
          fill="none"
          stroke={color}
          strokeWidth="1.2"
          opacity="0.8"
        >
          <animate attributeName="r" values="3;9;12" dur="2.2s" begin="0.7s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.8;0.2;0" dur="2.2s" begin="0.7s" repeatCount="indefinite" />
        </circle>

        {/* Solid Luminous Tip Bead */}
        <circle
          cx={lastPt.x}
          cy={lastPt.y}
          r="3.8"
          fill={color}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />

        {/* Hot white central core */}
        <circle
          cx={lastPt.x}
          cy={lastPt.y}
          r="1.6"
          fill="#FFFFFF"
        />
      </svg>
    </div>
  );
}
