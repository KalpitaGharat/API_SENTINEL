import React, { useState, useEffect } from 'react';
import { useScanContext } from '../context/ScanContext';
import apiClient from '../services/apiClient';

export default function SeverityDonutChart() {
  const { scans, allTimeAnalytics, refreshAllTimeAnalytics } = useScanContext();

  const [localAnalytics, setLocalAnalytics] = useState(allTimeAnalytics || null);
  const [centerCount, setCenterCount] = useState(0);
  const [hoveredIdx, setHoveredIdx] = useState(null);

  // Sync with ScanContext state or fetch directly if needed
  useEffect(() => {
    if (allTimeAnalytics && allTimeAnalytics.total_unique_findings !== undefined) {
      setLocalAnalytics(allTimeAnalytics);
    } else {
      let isMounted = true;
      apiClient.getAllTimeAnalytics()
        .then((data) => {
          if (isMounted && data) {
            setLocalAnalytics(data);
          }
        })
        .catch((err) => {
          console.warn('[SeverityDonutChart] Direct analytics fetch fallback error:', err);
        });
      return () => { isMounted = false; };
    }
  }, [allTimeAnalytics]);

  const totalScans = localAnalytics?.total_scans ?? (scans || []).length;
  const total = localAnalytics?.total_unique_findings ?? 0;
  const totalOccurrences = localAnalytics?.total_occurrences ?? total;
  const resolvedCount = localAnalytics?.resolved_findings ?? 0;
  const unresolvedCount = localAnalytics?.unresolved_findings ?? 0;

  const dist = localAnalytics?.severity_distribution || {};
  const pcts = localAnalytics?.severity_percentages || {};

  const critCount = dist.critical || 0;
  const highCount = dist.high || 0;
  const medCount = dist.medium || 0;
  const lowCount = dist.low || 0;
  const infoCount = dist.informational || 0;

  const critPct = pcts.critical ?? (total > 0 ? Math.round((critCount / total) * 100) : 0);
  const highPct = pcts.high ?? (total > 0 ? Math.round((highCount / total) * 100) : 0);
  const medPct = pcts.medium ?? (total > 0 ? Math.round((medCount / total) * 100) : 0);
  const lowPct = pcts.low ?? (total > 0 ? Math.round((lowCount / total) * 100) : 0);
  const infoPct = pcts.informational ?? (total > 0 ? Math.round((infoCount / total) * 100) : 0);

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
    }, 25);

    return () => clearInterval(interval);
  }, [total]);

  const segments = total === 0 ? [] : [
    { id: 'crit', label: 'Critical', count: critCount, percent: critPct, color: '#FF4D5E' },
    { id: 'high', label: 'High', count: highCount, percent: highPct, color: '#FF8A1F' },
    { id: 'med', label: 'Medium', count: medCount, percent: medPct, color: '#FFD21F' },
    { id: 'low', label: 'Low', count: lowCount, percent: lowPct, color: '#00E5FF' },
    ...(infoCount > 0 ? [{ id: 'info', label: 'Informational', count: infoCount, percent: infoPct, color: '#38BDF8' }] : []),
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#E8F1FF' }}>
            All-Time Vulnerability Distribution
          </span>
          <div style={{ fontSize: '12px', color: '#6482A6', marginTop: '2px' }}>
            Cumulative across {totalScans} {totalScans === 1 ? 'persisted scan' : 'persisted historical scans'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span
            style={{
              padding: '3px 9px',
              borderRadius: '6px',
              fontSize: '0.72rem',
              fontWeight: 700,
              background: 'rgba(0, 229, 255, 0.12)',
              border: '1px solid rgba(0, 229, 255, 0.35)',
              color: '#00E5FF',
              letterSpacing: '0.02em'
            }}
          >
            {totalScans} {totalScans === 1 ? 'Scan' : 'Scans'} Historical
          </span>
        </div>
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
            <div style={{ fontSize: '10px', color: '#8AA4C8', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Unique Findings
            </div>
            <div style={{ fontSize: '10px', color: '#00E5FF', marginTop: '2px', fontWeight: 600 }}>
              Across {totalScans} {totalScans === 1 ? 'Scan' : 'Scans'}
            </div>
          </div>
        </div>

        {/* Legend with Counts and Percentages */}
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="font-mono-code" style={{ color: '#FFFFFF', fontWeight: 700 }}>
                  {seg.count}
                </span>
                <span style={{ color: '#6482A6', fontSize: '11px' }}>
                  ({seg.percent}%)
                </span>
              </div>
            </div>
          ))}
          {total === 0 && (
            <div style={{ color: '#6482A6', fontSize: '12px', textAlign: 'center' }}>
              No vulnerabilities recorded across {totalScans} scans.
            </div>
          )}
        </div>
      </div>

      {/* Persistent Status & Deduplication Telemetry Footer */}
      <div
        style={{
          marginTop: '12px',
          paddingTop: '10px',
          borderTop: '1px solid rgba(15, 47, 78, 0.6)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.74rem',
          color: '#6482A6',
          flexWrap: 'wrap',
          gap: '6px',
        }}
      >
        <div>
          <span>Deduplicated from </span>
          <strong className="font-mono-code" style={{ color: '#E8F1FF' }}>{totalOccurrences}</strong>
          <span> detections</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span>Resolved: <strong style={{ color: '#22C55E' }}>{resolvedCount}</strong></span>
          <span>•</span>
          <span>Open: <strong style={{ color: '#FF4D5E' }}>{unresolvedCount}</strong></span>
        </div>
      </div>
    </div>
  );
}
