import React, { useState } from 'react';

/**
 * KpiCyberGraph - Factual Cyber Telemetry Sparkline
 * Plots real historical data points when available.
 * Never substitutes fabricated trajectory curves.
 */
export default function KpiCyberGraph({ 
  values = [],
  color = '#00E5FF',
  height = 42
}) {
  const [hoveredNode, setHoveredNode] = useState(null);

  // If no data points or empty dataset, render a clean, subtle flat baseline
  if (!values || values.length < 2) {
    return (
      <div 
        style={{ 
          width: '100%', 
          height: `${height}px`, 
          position: 'relative', 
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          userSelect: 'none'
        }}
      >
        <div 
          style={{
            width: '100%',
            height: '1px',
            background: `linear-gradient(90deg, transparent 0%, ${color}33 50%, transparent 100%)`,
          }}
        />
      </div>
    );
  }

  const rawValues = values.map((v) => Number(v) || 0);
  const minVal = Math.min(...rawValues);
  const maxVal = Math.max(...rawValues);
  const range = maxVal - minVal || 1;

  const width = 240;
  const padX = 10;
  const padTop = 6;
  const padBottom = 6;
  const drawW = width - padX * 2;
  const drawH = height - padTop - padBottom;

  const points = rawValues.map((v, i) => {
    const x = padX + (i / (rawValues.length - 1)) * drawW;
    const y = padTop + (1 - (v - minVal) / range) * drawH;
    return { x, y, val: v, idx: i };
  });

  // Natural cubic spline
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

  const lineD = createSpline(points);
  const areaD = `${lineD} L ${points[points.length - 1].x.toFixed(1)} ${height} L ${points[0].x.toFixed(1)} ${height} Z`;

  const gradId = `factualGrad_${color.replace('#', '')}`;

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
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Luminous Area */}
        <path d={areaD} fill={`url(#${gradId})`} />

        {/* Real Data Spline Line */}
        <path 
          d={lineD} 
          fill="none" 
          stroke={color} 
          strokeWidth="1.8" 
          strokeLinecap="round" 
        />

        {/* End Node */}
        {points.length > 0 && (
          <circle 
            cx={points[points.length - 1].x} 
            cy={points[points.length - 1].y} 
            r="3" 
            fill={color} 
          />
        )}
      </svg>
    </div>
  );
}
