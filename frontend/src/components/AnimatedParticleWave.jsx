import React, { useEffect, useRef } from 'react';

export default function AnimatedParticleWave({ width = 315, height = 180 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let time = 0;

    // Detect prefers-reduced-motion
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReducedMotion = mediaQuery.matches;

    // High DPI scaling
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Wave parameters
    const waves = [
      {
        amplitude: 22,
        frequency: 0.022,
        speed: 0.028,
        color: '#00D9F5',
        alpha: 0.85,
        lineWidth: 1.8,
        dotSpacing: 10,
        dotRadius: 2.2,
        glow: 8
      },
      {
        amplitude: 16,
        frequency: 0.032,
        speed: 0.035,
        color: '#168BFF',
        alpha: 0.55,
        lineWidth: 1.4,
        dotSpacing: 14,
        dotRadius: 1.8,
        glow: 5
      },
      {
        amplitude: 28,
        frequency: 0.018,
        speed: 0.02,
        color: '#36E4FB',
        alpha: 0.7,
        lineWidth: 1.2,
        dotSpacing: 12,
        dotRadius: 2.0,
        glow: 6
      }
    ];

    // Background floating dust particles
    const floaters = Array.from({ length: 18 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 1.5 + 0.8,
      speedY: Math.random() * 0.4 + 0.2,
      speedX: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.6 + 0.2
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw floating ambient cyber particles
      floaters.forEach((p) => {
        ctx.save();
        ctx.fillStyle = `rgba(0, 217, 245, ${p.alpha})`;
        ctx.shadowColor = '#00D9F5';
        ctx.shadowBlur = 4;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        if (!prefersReducedMotion) {
          p.y -= p.speedY;
          p.x += p.speedX;
          if (p.y < 0) {
            p.y = height;
            p.x = Math.random() * width;
          }
        }
      });

      // 2. Draw undulating 3D particle waves
      waves.forEach((wave, waveIdx) => {
        const baseY = height * 0.58 + waveIdx * 10;
        ctx.save();

        // Wave stroke
        ctx.strokeStyle = wave.color;
        ctx.globalAlpha = wave.alpha;
        ctx.lineWidth = wave.lineWidth;
        ctx.shadowColor = wave.color;
        ctx.shadowBlur = wave.glow;

        ctx.beginPath();
        let first = true;
        for (let x = -10; x <= width + 10; x += 3) {
          const y = baseY + Math.sin(x * wave.frequency + time * wave.speed + waveIdx * 1.5) * wave.amplitude
                          + Math.cos(x * 0.01 + time * 0.015) * 8;
          if (first) {
            ctx.moveTo(x, y);
            first = false;
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();

        // Glowing dots along the crests
        ctx.fillStyle = '#FFFFFF';
        for (let x = 0; x <= width; x += wave.dotSpacing) {
          const y = baseY + Math.sin(x * wave.frequency + time * wave.speed + waveIdx * 1.5) * wave.amplitude
                          + Math.cos(x * 0.01 + time * 0.015) * 8;
          ctx.beginPath();
          ctx.arc(x, y, wave.dotRadius, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.restore();
      });

      if (!prefersReducedMotion) {
        time += 1;
      }
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [width, height]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        display: 'block',
        pointerEvents: 'none',
      }}
    />
  );
}
