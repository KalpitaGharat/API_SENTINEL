import React, { useState } from 'react';

export default function ScanActivityChart() {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const dates = [
    'Oct 27', 'Oct 28', 'Oct 29', 'Oct 30', 'Oct 31',
    'Nov 01', 'Nov 02', 'Nov 03', 'Nov 04', 'Nov 05',
    'Nov 06', 'Nov 07', 'Nov 08', 'Nov 09'
  ];

  // Exact data points traced from Image 1:
  const values = [1.0, 1.8, 2.8, 2.0, 5.0, 3.0, 4.0, 7.2, 4.8, 4.2, 5.0, 6.4, 4.6, 5.8];

  // SVG viewBox geometry calibrated for 1600x900 viewport
  const width = 680;
  const height = 200;
  const padLeft = 30;
  const padRight = 20;
  const padTop = 18;
  const padBottom = 28;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const maxVal = 10;

  const points = values.map((val, idx) => {
    const x = padLeft + (idx / (values.length - 1)) * chartW;
    const y = padTop + (1 - val / maxVal) * chartH;
    return { x, y, val, date: dates[idx], idx };
  });

  // Silky smooth natural spline (tension = 0.32)
  const createSpline = (pts, tension = 0.32) => {
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
  const areaD = `${lineD} L ${points[points.length - 1].x.toFixed(1)} ${(padTop + chartH).toFixed(1)} L ${points[0].x.toFixed(1)} ${(padTop + chartH).toFixed(1)} Z`;

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
        animation: 'bootCascade 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards 420ms'
      }}
    >
      {/* Header matching Image 1 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '16px', fontWeight: 700, color: '#FFFFFF', letterSpacing: '-0.01em' }}>
            Scan Activity
          </span>
          <span style={{ fontSize: '14px', fontWeight: 500, color: '#8AA4C8' }}>
            (Last 14 Days)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#FFFFFF', fontWeight: 500 }}>
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
          <span style={{ fontSize: '13px', color: '#E8F1FF' }}>Scans Run</span>
        </div>
      </div>

      {/* SVG Chart */}
      <div style={{ position: 'relative', width: '100%', height: '190px' }}>
        <svg 
          viewBox={`0 0 ${width} ${height}`} 
          style={{ width: '100%', height: '100%', overflow: 'visible' }}
          onMouseLeave={() => setHoveredPoint(null)}
        >
          <defs>
            {/* Luminous cyan area glow gradient */}
            <linearGradient id="scanAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.28" />
              <stop offset="60%" stopColor="#00E5FF" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.0" />
            </linearGradient>

            {/* Cyan glow for line */}
            <filter id="cyanLineGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#00E5FF" floodOpacity="0.6" />
            </filter>
          </defs>

          {/* Faint Horizontal Gridlines: Y 0 to 10, step 2 (matching Image 1) */}
          {[0, 2, 4, 6, 8, 10].map((yTick) => {
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
                  x={padLeft - 9}
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

          {/* X-Axis Dates in Inter (matching Image 1) */}
          {points.map((pt, i) => (
            <text
              key={i}
              x={pt.x}
              y={padTop + chartH + 19}
              fill="#7892B0"
              fontSize="10"
              fontFamily="'Inter', -apple-system, sans-serif"
              fontWeight="500"
              textAnchor="middle"
            >
              {pt.date}
            </text>
          ))}

          {/* Area under the line */}
          <path
            d={areaD}
            fill="url(#scanAreaGrad)"
          />

          {/* Main Spline line (pure luminous cyan) */}
          <path
            d={lineD}
            fill="none"
            stroke="#00E5FF"
            strokeWidth="2.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#cyanLineGlow)"
          />

          {/* Vertical hover crosshair */}
          {hoveredPoint && (
            <line
              x1={hoveredPoint.x}
              y1={padTop}
              x2={hoveredPoint.x}
              y2={padTop + chartH}
              stroke="rgba(0, 229, 255, 0.5)"
              strokeWidth="1.2"
              strokeDasharray="3 3"
            />
          )}

          {/* Solid Glowing Cyan Dots on EVERY Data Point (matching Image 1) */}
          {points.map((pt, i) => {
            const isHovered = hoveredPoint?.idx === pt.idx;
            return (
              <g
                key={i}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredPoint(pt)}
              >
                {/* Generous hover hit target */}
                <circle cx={pt.x} cy={pt.y} r={14} fill="transparent" />

                {/* Outer halo ripple on hover */}
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={9}
                    fill="none"
                    stroke="#00E5FF"
                    strokeWidth="1.5"
                    opacity="0.8"
                  />
                )}

                {/* Solid luminous cyan bead matching Image 1 */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isHovered ? 5.5 : 4}
                  fill="#00E5FF"
                  style={{
                    filter: isHovered 
                      ? 'drop-shadow(0 0 10px #00E5FF)' 
                      : 'drop-shadow(0 0 4px rgba(0, 229, 255, 0.8))',
                    transition: 'all 0.15s ease'
                  }}
                />

                {/* White specular center on hover */}
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={2}
                    fill="#FFFFFF"
                  />
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            style={{
              position: 'absolute',
              left: `${(hoveredPoint.x / width) * 100}%`,
              top: `${Math.max(0, (hoveredPoint.y / height) * 100 - 36)}%`,
              transform: 'translate(-50%, -100%)',
              background: 'rgba(6, 20, 38, 0.95)',
              border: '1px solid #00E5FF',
              borderRadius: '6px',
              padding: '6px 10px',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.6), 0 0 10px rgba(0, 229, 255, 0.4)',
              pointerEvents: 'none',
              zIndex: 30,
              whiteSpace: 'nowrap',
              fontSize: '11px',
              display: 'flex',
              flexDirection: 'column',
              gap: '2px'
            }}
          >
            <div style={{ color: '#8AA4C8', fontSize: '10px' }}>{hoveredPoint.date}</div>
            <div style={{ color: '#00E5FF', fontWeight: 700, fontSize: '13px' }}>
              {hoveredPoint.val} <span style={{ color: '#E8F1FF', fontSize: '11px', fontWeight: 500 }}>scans</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
