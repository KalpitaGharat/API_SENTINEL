import React, { useEffect, useRef } from 'react';

export default function LiveCyberSparkline({ 
  type = 'scans', // 'scans' | 'threat' | 'fixed' | 'health'
  color = '#3B82F6',
  accentColor = '#19D3FF',
  height = 36 
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let isVisible = true;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReducedMotion = mediaQuery.matches;

    const dpr = window.devicePixelRatio || 1;
    let rect = canvas.getBoundingClientRect();
    let width = rect.width || 220;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const handleResize = () => {
      if (!canvas) return;
      rect = canvas.getBoundingClientRect();
      width = rect.width || 220;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
    };
    window.addEventListener('resize', handleResize);

    const handleVisibilityChange = () => {
      isVisible = !document.hidden;
      if (isVisible && !prefersReducedMotion) {
        render();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    let time = 0;

    const render = () => {
      if (!isVisible) return;
      ctx.clearRect(0, 0, width, height);
      time += 0.035;

      // Compute smooth, silky flowing wave points
      const pointCount = 30;
      const pts = [];
      const midY = height * 0.52;
      const amp = height * 0.28;

      for (let i = 0; i < pointCount; i++) {
        const u = i / (pointCount - 1);
        const x = u * width;
        let y = midY;

        if (type === 'scans') {
          // Flowing dual-frequency cyber wave
          const w1 = Math.sin(u * 7 - time * 2.2) * amp;
          const w2 = Math.cos(u * 12 + time * 1.4) * (amp * 0.35);
          y = midY + w1 + w2;
        } else if (type === 'threat') {
          // Elevated dynamic threat pulse with controlled harmonic peaks
          const w1 = Math.sin(u * 8 - time * 2.6) * amp;
          const w2 = Math.sin(u * 14 - time * 3.8) * (amp * 0.4);
          y = midY + w1 + w2;
        } else if (type === 'fixed') {
          // Ascending rhythm towards the right
          const w1 = Math.sin(u * 6 - time * 2.0) * amp;
          const incline = (0.5 - u) * (amp * 0.6);
          y = midY + w1 + incline;
        } else {
          // Stable, rhythmic security health frequency
          const w1 = Math.sin(u * 6 - time * 1.8) * amp;
          const w2 = Math.cos(u * 9 + time * 1.2) * (amp * 0.3);
          y = midY + w1 + w2;
        }

        // Keep smoothly clamped within margins
        y = Math.max(3, Math.min(height - 3, y));
        pts.push({ x, y });
      }

      // 1. Draw glowing gradient fill under curve
      ctx.save();
      const grad = ctx.createLinearGradient(0, 0, 0, height);
      grad.addColorStop(0, color);
      grad.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 0; i < pts.length - 1; i++) {
        const xc = (pts[i].x + pts[i + 1].x) / 2;
        const yc = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, xc, yc);
      }
      ctx.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
      ctx.lineTo(width, height);
      ctx.lineTo(0, height);
      ctx.closePath();

      ctx.fillStyle = grad;
      ctx.globalAlpha = 0.18;
      ctx.fill();
      ctx.restore();

      // 2. Draw soft neon glow line
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 4;
      ctx.globalAlpha = 0.3;
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 0; i < pts.length - 1; i++) {
        const xc = (pts[i].x + pts[i + 1].x) / 2;
        const yc = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, xc, yc);
      }
      ctx.stroke();
      ctx.restore();

      // 3. Draw crisp main wave line
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.8;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 0; i < pts.length - 1; i++) {
        const xc = (pts[i].x + pts[i + 1].x) / 2;
        const yc = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, xc, yc);
      }
      ctx.stroke();
      ctx.restore();

      // 4. Draw leading tip telemetry beacon at the rightmost point
      const lastPt = pts[pts.length - 1];
      const pulseSize = 2.5 + Math.sin(time * 6) * 1;

      // Glow halo
      ctx.save();
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.4;
      ctx.beginPath();
      ctx.arc(lastPt.x - 2, lastPt.y, pulseSize + 3, 0, Math.PI * 2);
      ctx.fill();

      // Center bright beacon
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#FFFFFF';
      ctx.beginPath();
      ctx.arc(lastPt.x - 2, lastPt.y, pulseSize, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      cancelAnimationFrame(animationFrameId);
    };
  }, [type, color, accentColor, height]);

  return (
    <div style={{ width: '100%', height: `${height}px`, position: 'relative', overflow: 'hidden' }}>
      <canvas 
        ref={canvasRef} 
        style={{ width: '100%', height: `${height}px`, display: 'block' }}
      />
    </div>
  );
}
