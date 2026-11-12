import React, { useState, useEffect } from 'react';
import { useScanContext } from '../context/ScanContext';

export default function SeverityDonutChart() {
  const { findings } = useScanContext();

  const total = (findings || []).length;
  const crit = (findings || []).filter((f) => (f.severity || '').toLowerCase() === 'critical').length;
  const high = (findings || []).filter((f) => (f.severity || '').toLowerCase() === 'high').length;
  const med = (findings || []).filter((f) => (f.severity || '').toLowerCase() === 'medium').length;
  const low = (findings || []).filter((f) => (f.severity || '').toLowerCase() === 'low' || (f.severity || '').toLowerCase() === 'informational').length;

  const [centerCount, setCenterCount] = useState(0);
  const [hoveredIdx, setHoveredIdx] = useState(null);

  useEffect(() => {
    let current = 0;
    const target = total;
    if (target === 0) {
      setCenterCount(0);
      return;
    }
    const interval = setInterval(() => {
      current++;
      setCenterCount(current);
      if (current >= target) clearInterval(interval);
    }, 30);

    return () => clearInterval(interval);
  }, [total]);

  const segments = total === 0 ? [] : [
    { id: 'crit', label: 'Critical', count: crit, percent: Math.round((crit / total) * 100), color: '#FF4D5E' },
    { id: 'high', label: 'High', count: high, percent: Math.round((high / total) * 100), color: '#FF8A1F' },
    { id: 'med', label: 'Medium', count: med, percent: Math.round((med / total) * 100), color: '#FFD21F' },
    { id: 'low', label: 'Low', count: low, percent: Math.round((low / total) * 100), color: '#00E5FF' },
  ];

  // Geometry
  const radius = 60;
  const strokeWidth = 24;
  const circumference = 2 * Math.PI * radius;
  const gap = total > 1 ? 3 : 0;

  let accumulatedPercent = 0;
  const renderedSegments = segments.map((seg, idx) => {
    const segLength = Math.max(0, (seg.percent / 100) * circumference - gap);
    const offset = -(accumulatedPercent / 100) * circumference;
    accumulatedPercent += seg.percent;
    return { ...seg, segLength, offset, idx };
  });

  return (
    <div 
      className="cyber-card"
      style={{
        padding: '22px 24px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#E8F1FF' }}>
          Vulnerability Severity Distribution
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', marginTop: '4px' }}>
        {/* Dynamic Vector Donut */}
        <div style={{ position: 'relative', width: '160px', height: '160px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <svg viewBox="0 0 170 170" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)', overflow: 'visible' }}>
            <circle
              cx="85"
              cy="85"
              r={radius}
              fill="transparent"
              stroke="#08182B"
              strokeWidth={strokeWidth}
            />
            {renderedSegments.map((seg) => (
              <circle
                key={seg.id}
                cx="85"
                cy="85"
                r={radius}
                fill="transparent"
                stroke={seg.color}
                strokeWidth={strokeWidth}
                strokeDasharray={`${seg.segLength} ${circumference}`}
                strokeDashoffset={seg.offset}
                strokeLinecap="round"
                onMouseEnter={() => setHoveredIdx(seg.idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{
                  transition: 'all 0.3s ease',
                  cursor: 'pointer',
                  filter: hoveredIdx === seg.idx ? `drop-shadow(0 0 8px ${seg.color})` : 'none',
                }}
              />
            ))}
          </svg>

          {/* Center Callout */}
          <div style={{ position: 'absolute', textAlign: 'center', pointerEvents: 'none' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
              {centerCount}
            </div>
            <div style={{ fontSize: '11px', color: '#8AA4C8', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Findings
            </div>
          </div>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          {segments.map((seg) => (
            <div 
              key={seg.id}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                fontSize: '12px',
                padding: '4px 6px',
                borderRadius: '4px',
                background: hoveredIdx === seg.idx ? 'rgba(0, 229, 255, 0.08)' : 'transparent',
              }}
              onMouseEnter={() => setHoveredIdx(seg.idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: seg.color }} />
                <span style={{ color: '#8AA4C8' }}>{seg.label}</span>
              </div>
              <span className="font-mono-code" style={{ color: '#FFFFFF', fontWeight: 700 }}>
                {seg.count}
              </span>
            </div>
          ))}
          {total === 0 && (
            <div style={{ color: '#6482A6', fontSize: '12px', textAlign: 'center' }}>
              No findings recorded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
