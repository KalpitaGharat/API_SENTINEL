import React, { useEffect, useRef } from 'react';

export default function AmbientCyberBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let isTabVisible = true;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReducedMotion = mediaQuery.matches;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const handleVisibilityChange = () => {
      isTabVisible = !document.hidden;
      if (isTabVisible && !prefersReducedMotion) {
        lastTime = performance.now();
        render();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 50 tiny glowing particles floating upward with twinkle
    const colors = ['#19D3FF', '#8B5CF6', '#FFFFFF', '#14B8A6'];
    const particleCount = 52;
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      speedY: Math.random() * 0.45 + 0.15,
      speedX: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 2 + 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: Math.random() * 0.6 + 0.2,
      twinkleSpeed: Math.random() * 0.04 + 0.015,
      twinklePhase: Math.random() * Math.PI * 2,
    }));

    let lastTime = performance.now();

    const render = () => {
      if (!isTabVisible) return;
      ctx.clearRect(0, 0, width, height);

      particles.forEach((p) => {
        p.twinklePhase += p.twinkleSpeed;
        const currentAlpha = Math.max(0.08, p.alpha + Math.sin(p.twinklePhase) * 0.25);

        ctx.save();
        ctx.fillStyle = p.color;
        ctx.globalAlpha = currentAlpha;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        if (!prefersReducedMotion) {
          p.y -= p.speedY;
          p.x += p.speedX;

          if (p.y < -10) {
            p.y = height + 10;
            p.x = Math.random() * width;
          }
          if (p.x < -10) p.x = width + 10;
          if (p.x > width + 10) p.x = -10;
        }
      });

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, []);

  const hexLines = [
    '0x1F4A  SYN_ACK',
    'GET /api/users 200',
    'POST /api/login 401',
    'AUTH_JWT_VALID',
    '0x7FE9  TLSv1.3',
    'BOLA_PROBE_PASS',
    '200 OK [42ms]',
    '0xA03C  CRYPTO_AES',
    'RATE_LIMIT 429',
    '0x88B1  HASH_SHA256',
    'WAF_INSPECT_PASS',
    '0xC21E  REST_GATEWAY',
    'CORS_ORIGIN_VERIFIED',
    '0x3E11  SEC_AUDIT'
  ];

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
        overflow: 'hidden'
      }}
    >
      {/* a) Base Dark Navy Gradient (#040813 -> #071a33) with Drifting Radial Auras */}
      <div 
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, #040813 0%, #061124 50%, #071A33 100%)'
        }}
      />

      {/* Cyan top-right drifting aura */}
      <div 
        style={{
          position: 'absolute',
          top: '-10%',
          right: '-5%',
          width: '750px',
          height: '750px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(25, 211, 255, 0.11) 0%, rgba(22, 139, 255, 0.04) 50%, transparent 75%)',
          filter: 'blur(50px)',
          animation: 'auraDrift1 35s ease-in-out infinite alternate'
        }}
      />

      {/* Violet bottom-left drifting aura */}
      <div 
        style={{
          position: 'absolute',
          bottom: '-15%',
          left: '10%',
          width: '700px',
          height: '700px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.09) 0%, rgba(20, 184, 166, 0.03) 50%, transparent 75%)',
          filter: 'blur(60px)',
          animation: 'auraDrift2 40s ease-in-out infinite alternate'
        }}
      />

      {/* Teal center-left aura behind charts */}
      <div 
        style={{
          position: 'absolute',
          top: '35%',
          left: '30%',
          width: '650px',
          height: '650px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(20, 184, 166, 0.06) 0%, transparent 70%)',
          filter: 'blur(45px)',
          animation: 'auraDrift3 32s ease-in-out infinite alternate'
        }}
      />

      {/* b) Cyber Grid: 1px lines at ~4% opacity, 48px cells, radial masked */}
      <div 
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(25, 211, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(25, 211, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse 90% 85% at 50% 50%, black 40%, transparent 100%)',
          WebkitMaskImage: 'radial-gradient(ellipse 90% 85% at 50% 50%, black 40%, transparent 100%)',
        }}
      />

      {/* c) Particle Canvas (Twinkling floating particles) */}
      <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0 }} />

      {/* d) Monospace Hex & Log Stream along right edge (~6% opacity) */}
      <div 
        className="font-mono-code hex-logs-stream"
        style={{
          position: 'absolute',
          top: 0,
          right: '24px',
          width: '180px',
          fontSize: '10px',
          lineHeight: '2.2',
          color: 'rgba(25, 211, 255, 0.08)',
          userSelect: 'none',
          whiteSpace: 'nowrap'
        }}
      >
        {[...hexLines, ...hexLines, ...hexLines, ...hexLines].map((line, idx) => (
          <div key={idx}>{line}</div>
        ))}
      </div>

      {/* e) Top-Right Wireframe Globe with rotating dashed orbit rings (SVG - unmuted) */}
      <div 
        style={{
          position: 'absolute',
          top: '-40px',
          right: '80px',
          width: '320px',
          height: '320px',
          opacity: 0.75,
          pointerEvents: 'none'
        }}
      >
        <svg viewBox="0 0 200 200" style={{ width: '100%', height: '100%' }}>
          <defs>
            <radialGradient id="globeGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#19D3FF" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#19D3FF" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Globe core */}
          <circle cx="100" cy="100" r="48" fill="url(#globeGlow)" stroke="#19D3FF" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
          
          {/* Latitude & Longitude wires */}
          <ellipse cx="100" cy="100" rx="48" ry="18" fill="none" stroke="#19D3FF" strokeWidth="0.8" opacity="0.7" />
          <ellipse cx="100" cy="100" rx="48" ry="34" fill="none" stroke="#19D3FF" strokeWidth="0.8" opacity="0.5" />
          <line x1="100" y1="52" x2="100" y2="148" stroke="#19D3FF" strokeWidth="0.8" strokeDasharray="2 2" opacity="0.6" />
          <line x1="52" y1="100" x2="148" y2="100" stroke="#19D3FF" strokeWidth="0.8" strokeDasharray="2 2" opacity="0.6" />

          {/* Rotating Dashed Orbit Ring 1 */}
          <ellipse 
            cx="100" 
            cy="100" 
            rx="78" 
            ry="30" 
            fill="none" 
            stroke="#19D3FF" 
            strokeWidth="1.8" 
            strokeDasharray="6 4" 
            className="globe-ring-1"
            style={{ filter: 'drop-shadow(0 0 6px rgba(25, 211, 255, 0.8))' }}
          />

          {/* Orbiting Beacon Dot */}
          <circle cx="178" cy="100" r="3.5" fill="#19D3FF" className="globe-ring-1" style={{ filter: 'drop-shadow(0 0 8px #19D3FF)' }}>
            <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
          </circle>

          {/* Rotating Dashed Orbit Ring 2 */}
          <ellipse 
            cx="100" 
            cy="100" 
            rx="36" 
            ry="88" 
            fill="none" 
            stroke="#8B5CF6" 
            strokeWidth="1.6" 
            strokeDasharray="5 5" 
            className="globe-ring-2"
            style={{ filter: 'drop-shadow(0 0 6px rgba(139, 92, 246, 0.8))' }}
          />
        </svg>
      </div>

      {/* f) Faint Horizontal Scanline Sweeping down every ~8s */}
      <div className="ambient-scanline" />

      {/* Vignette Overlay */}
      <div 
        style={{
          position: 'absolute',
          inset: 0,
          boxShadow: 'inset 0 0 120px rgba(2, 6, 16, 0.85)'
        }}
      />
    </div>
  );
}