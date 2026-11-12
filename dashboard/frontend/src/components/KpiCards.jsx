import React, { useState, useEffect } from 'react';
import { Target, AlertTriangle, CheckCircle, ShieldCheck, Info } from 'lucide-react';
import KpiCyberGraph from './KpiCyberGraph';
import { useScanContext } from '../context/ScanContext';

export default function KpiCards() {
  const { scans, findings } = useScanContext();

  const totalScans = scans?.length || 0;
  const openVulns = (findings || []).filter((f) => f.status !== 'Resolved').length;
  const fixedVulns = (findings || []).filter((f) => f.status === 'Resolved').length;
  const totalFindings = (findings || []).length;

  const crit = (findings || []).filter((f) => f.severity === 'Critical' && f.status !== 'Resolved').length;
  const high = (findings || []).filter((f) => f.severity === 'High' && f.status !== 'Resolved').length;
  const med = (findings || []).filter((f) => f.severity === 'Medium' && f.status !== 'Resolved').length;
  const low = (findings || []).filter((f) => f.severity === 'Low' && f.status !== 'Resolved').length;

  const targetHealth = totalFindings === 0 
    ? 100 
    : Math.max(10, Math.min(100, Math.round(100 - (crit * 25 + high * 15 + med * 8 + low * 3) + (fixedVulns * 10))));

  const [counts, setCounts] = useState({
    scans: 0,
    vulns: 0,
    fixed: 0,
    health: 0,
  });

  useEffect(() => {
    const targets = { 
      scans: totalScans, 
      vulns: openVulns, 
      fixed: fixedVulns, 
      health: targetHealth 
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
        vulns: Math.round(targets.vulns * ease),
        fixed: Math.round(targets.fixed * ease),
        health: Math.round(targets.health * ease),
      });

      if (step >= steps) {
        clearInterval(timer);
      }
    }, intervalTime);

    return () => clearInterval(timer);
  }, [totalScans, openVulns, fixedVulns, targetHealth]);

  return (
    <div 
      className="kpi-grid"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '18px',
        marginBottom: '20px',
      }}
    >
      {/* 1. Total Scans */}
      <div 
        className="cyber-card"
        style={{
          background: 'linear-gradient(135deg, rgba(14, 45, 90, 0.45) 0%, rgba(8, 24, 48, 0.55) 100%)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(0, 180, 255, 0.22)',
          borderRadius: '14px',
          padding: '20px 22px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#8AA4C8', letterSpacing: '0.02em' }}>
            TOTAL SCANS
          </span>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(0, 229, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Target size={18} color="#00E5FF" />
          </div>
        </div>
        <div style={{ fontSize: '32px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
          {counts.scans}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', fontSize: '12px', color: '#00E5FF' }}>
          <span>Active Registry Sessions</span>
        </div>
        <KpiCyberGraph theme="blue" />
      </div>

      {/* 2. Open Vulnerabilities */}
      <div 
        className="cyber-card"
        style={{
          background: 'linear-gradient(135deg, rgba(70, 20, 25, 0.45) 0%, rgba(30, 8, 12, 0.55) 100%)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 77, 94, 0.25)',
          borderRadius: '14px',
          padding: '20px 22px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#FF8A98', letterSpacing: '0.02em' }}>
            OPEN FINDINGS
          </span>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(255, 77, 94, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AlertTriangle size={18} color="#FF4D5E" />
          </div>
        </div>
        <div style={{ fontSize: '32px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
          {counts.vulns}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', fontSize: '12px', color: '#FF8A98' }}>
          <span>{crit} Critical / {high} High</span>
        </div>
        <KpiCyberGraph theme="red" />
      </div>

      {/* 3. Remediated & Verified */}
      <div 
        className="cyber-card"
        style={{
          background: 'linear-gradient(135deg, rgba(16, 60, 36, 0.45) 0%, rgba(8, 28, 18, 0.55) 100%)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(34, 197, 94, 0.25)',
          borderRadius: '14px',
          padding: '20px 22px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#86EFAC', letterSpacing: '0.02em' }}>
            VERIFIED RESOLVED
          </span>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(34, 197, 94, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CheckCircle size={18} color="#22C55E" />
          </div>
        </div>
        <div style={{ fontSize: '32px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
          {counts.fixed}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', fontSize: '12px', color: '#22C55E' }}>
          <span>Passed Retest Probes</span>
        </div>
        <KpiCyberGraph theme="green" />
      </div>

      {/* 4. Security Health Score */}
      <div 
        className="cyber-card"
        style={{
          background: 'linear-gradient(135deg, rgba(60, 45, 14, 0.45) 0%, rgba(28, 20, 6, 0.55) 100%)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 210, 31, 0.25)',
          borderRadius: '14px',
          padding: '20px 22px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#FDE047', letterSpacing: '0.02em' }}>
            HEALTH SCORE
          </span>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(255, 210, 31, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={18} color="#FFD21F" />
          </div>
        </div>
        <div style={{ fontSize: '32px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
          {counts.health}<span style={{ fontSize: '18px', color: '#8AA4C8', fontWeight: 600 }}>/100</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', fontSize: '12px', color: '#FFD21F' }}>
          <span>OWASP Top 10 Compliance</span>
        </div>
        <KpiCyberGraph theme="orange" />
      </div>
    </div>
  );
}
