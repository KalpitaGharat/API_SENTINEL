/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          DEFAULT: '#040d1a',
          deep: '#06101e',
          darker: '#020914',
        },
        surface: {
          DEFAULT: '#0a182c',
          card: '#0d1f38',
          hover: '#102544',
          border: '#132b4f',
        },
        cyber: {
          cyan: '#00f2fe',
          glow: 'rgba(0, 242, 254, 0.2)',
          blue: '#168bff',
          electric: '#00c6ff',
        },
        severity: {
          critical: '#ff4d4f',
          'critical-bg': 'rgba(255, 77, 79, 0.15)',
          high: '#fa8c16',
          'high-bg': 'rgba(250, 140, 22, 0.15)',
          medium: '#fadb14',
          'medium-bg': 'rgba(250, 219, 20, 0.15)',
          low: '#13c2c2',
          'low-bg': 'rgba(19, 194, 194, 0.15)',
          fixed: '#52c41a',
          'fixed-bg': 'rgba(82, 196, 26, 0.15)',
        }
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        radarSweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pulseBeacon: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(255, 77, 79, 0.5)' },
          '50%': { opacity: '0.88', transform: 'scale(1.02)', boxShadow: '0 0 12px 2px rgba(255, 77, 79, 0.35)' },
        },
        nodeBreathe: {
          '0%, 100%': { r: '4', filter: 'drop-shadow(0 0 3px rgba(0, 242, 254, 0.6))' },
          '50%': { r: '5.5', filter: 'drop-shadow(0 0 10px rgba(0, 242, 254, 0.95))' },
        },
        strokeDraw: {
          '0%': { strokeDashoffset: '408.4' },
          '100%': { strokeDashoffset: '0' },
        },
        clipReveal: {
          '0%': { clipPath: 'inset(0 100% 0 0)' },
          '100%': { clipPath: 'inset(0 0% 0 0)' },
        }
      },
      animation: {
        fadeInUp: 'fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        radar: 'radarSweep 4s linear infinite',
        beacon: 'pulseBeacon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        breathe: 'nodeBreathe 3s ease-in-out infinite',
        clipDraw: 'clipReveal 1.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }
    },
  },
  plugins: [],
}
