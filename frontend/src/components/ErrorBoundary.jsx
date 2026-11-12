import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[API Sentinel ErrorBoundary caught exception]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          style={{
            padding: '30px',
            borderRadius: '12px',
            background: 'rgba(255, 77, 94, 0.08)',
            border: '1px solid rgba(255, 77, 94, 0.35)',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
            color: '#FFFFFF',
            margin: '20px 0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <AlertOctagon size={24} color="#FF4D5E" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#FF4D5E', margin: 0 }}>
              {this.props.title || 'Component Error Intercepted'}
            </h3>
          </div>
          <p style={{ color: '#8AA4C8', fontSize: '0.9rem', lineHeight: '1.6', marginBottom: '16px' }}>
            An unexpected error occurred while rendering this module. The rest of the dashboard remains operational.
          </p>
          {this.state.error && (
            <pre
              style={{
                background: '#040F1E',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid #0F2F4E',
                color: '#FF8A1F',
                fontSize: '0.8rem',
                fontFamily: 'JetBrains Mono, monospace',
                overflowX: 'auto',
                marginBottom: '16px',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}
            >
              {this.state.error.toString()}
            </pre>
          )}
          <button
            onClick={this.handleReset}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              background: '#00E5FF',
              color: '#040813',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <RotateCcw size={16} />
            <span>Reload Module</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
