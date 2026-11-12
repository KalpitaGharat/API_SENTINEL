import React, { useState } from 'react';
import { 
  Sparkles, 
  RefreshCw, 
  ShieldCheck, 
  AlertTriangle, 
  Code, 
  Cpu, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  History,
  FileCode2,
  Lock,
  Layers
} from 'lucide-react';
import apiClient from '../services/apiClient';

export default function AiExplanationPanel({ finding, onExplanationUpdated }) {
  const [explanation, setExplanation] = useState(finding?.ai_explanation || null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState(null);
  const [isCached, setIsCached] = useState(Boolean(finding?.ai_explanation));
  const [activeTab, setActiveTab] = useState('summary'); // summary, impact, remediation

  const handleExplain = async (forceRefresh = false) => {
    if (!finding?.id) return;
    if (forceRefresh) {
      setIsRegenerating(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const data = await apiClient.explainFinding(finding.id, forceRefresh);
      setExplanation(data);
      setIsCached(!forceRefresh);
      if (onExplanationUpdated) {
        onExplanationUpdated(finding.id, data);
      }
    } catch (err) {
      console.error('[AiExplanationPanel] Failed to generate explanation:', err);
      const msg = err?.details?.detail || err?.message || 'Failed to communicate with AI explanation service.';
      setError(msg);
    } finally {
      setIsLoading(false);
      setIsRegenerating(false);
    }
  };

  // Determine model status badge
  const isNemotron = explanation?.model_name?.toLowerCase().includes('nemotron') || 
                    explanation?.model_name?.toLowerCase().includes('nvidia');
  const isFallback = explanation?.model_name?.toLowerCase().includes('rule-based') ||
                     explanation?.model_name?.toLowerCase().includes('fallback');

  return (
    <div 
      style={{
        marginTop: '20px',
        padding: '22px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(6, 18, 38, 0.85) 100%)',
        border: '1px solid rgba(139, 92, 246, 0.35)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45), 0 0 20px rgba(139, 92, 246, 0.12)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top Banner Accent */}
      <div 
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #8B5CF6 0%, #00E5FF 50%, #8B5CF6 100%)',
        }}
      />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div 
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(139, 92, 246, 0.4)'
            }}
          >
            <Sparkles size={18} color="#C084FC" />
          </div>
          <div>
            <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#FFFFFF', margin: 0, letterSpacing: '0.3px' }}>
              AI-POWERED SECURITY ANALYSIS
            </h4>
            <span style={{ fontSize: '0.74rem', color: '#8AA4C8' }}>
              NVIDIA Nemotron 30B Reasoning LLM & Offline Safety Guard
            </span>
          </div>
        </div>

        {/* Model & Source Badge */}
        {explanation && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 700,
                background: isNemotron ? 'rgba(139, 92, 246, 0.2)' : 'rgba(0, 229, 255, 0.15)',
                color: isNemotron ? '#C084FC' : '#00E5FF',
                border: `1px solid ${isNemotron ? 'rgba(139, 92, 246, 0.45)' : 'rgba(0, 229, 255, 0.35)'}`,
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              <Cpu size={12} />
              <span>{isNemotron ? 'NVIDIA Nemotron (Live AI)' : (isFallback ? 'Deterministic Rule Engine' : explanation.model_name)}</span>
            </span>

            {isCached && (
              <span
                style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  background: 'rgba(138, 164, 200, 0.12)',
                  color: '#8AA4C8',
                  border: '1px solid rgba(138, 164, 200, 0.25)',
                }}
              >
                Cached in SQLite
              </span>
            )}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {!explanation && !isLoading ? (
        /* Empty State / Initial CTA */
        <div 
          style={{
            padding: '28px 20px',
            textAlign: 'center',
            background: 'rgba(7, 24, 43, 0.6)',
            borderRadius: '10px',
            border: '1px dashed rgba(139, 92, 246, 0.3)',
          }}
        >
          <p style={{ color: '#8AA4C8', fontSize: '0.88rem', marginBottom: '16px', maxWidth: '520px', margin: '0 auto 18px auto' }}>
            Generate plain-English vulnerability breakdown, real-world attack scenarios, business impact, and code-level remediation using NVIDIA Nemotron.
          </p>
          <button
            onClick={() => handleExplain(false)}
            disabled={isLoading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '11px 22px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
              color: '#FFFFFF',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              boxShadow: '0 0 20px rgba(139, 92, 246, 0.5)',
              transition: 'all 0.2s ease',
            }}
          >
            <Sparkles size={16} />
            <span>Explain with Nemotron AI</span>
          </button>
        </div>
      ) : isLoading ? (
        /* Animated Cyber Loading Skeleton */
        <div style={{ padding: '24px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', color: '#C084FC' }}>
            <RefreshCw size={18} className="animate-spin" />
            <span style={{ fontSize: '0.86rem', fontWeight: 600 }}>
              Querying NVIDIA Nemotron-3.5-Lightning Reasoning Model...
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ height: '14px', width: '85%', background: 'rgba(139, 92, 246, 0.15)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
            <div style={{ height: '14px', width: '92%', background: 'rgba(139, 92, 246, 0.15)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
            <div style={{ height: '14px', width: '70%', background: 'rgba(139, 92, 246, 0.15)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
            <div style={{ height: '60px', width: '100%', background: 'rgba(0, 229, 255, 0.08)', borderRadius: '6px', marginTop: '8px', animation: 'pulse 1.5s infinite' }} />
          </div>
        </div>
      ) : (
        /* Rendered Explanation View */
        <div>
          {/* Navigation Tabs */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid rgba(139, 92, 246, 0.25)', paddingBottom: '10px' }}>
            <button
              onClick={() => setActiveTab('summary')}
              style={{
                background: activeTab === 'summary' ? 'rgba(139, 92, 246, 0.25)' : 'transparent',
                border: activeTab === 'summary' ? '1px solid #8B5CF6' : '1px solid transparent',
                color: activeTab === 'summary' ? '#FFFFFF' : '#8AA4C8',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Vulnerability Breakdown
            </button>
            <button
              onClick={() => setActiveTab('impact')}
              style={{
                background: activeTab === 'impact' ? 'rgba(139, 92, 246, 0.25)' : 'transparent',
                border: activeTab === 'impact' ? '1px solid #8B5CF6' : '1px solid transparent',
                color: activeTab === 'impact' ? '#FFFFFF' : '#8AA4C8',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Attack Scenarios & Impact
            </button>
            <button
              onClick={() => setActiveTab('remediation')}
              style={{
                background: activeTab === 'remediation' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                border: activeTab === 'remediation' ? '1px solid #00E5FF' : '1px solid transparent',
                color: activeTab === 'remediation' ? '#00E5FF' : '#8AA4C8',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Step-by-Step Remediation
            </button>
          </div>

          {/* Tab Content Panes */}
          <div style={{ minHeight: '140px' }}>
            {activeTab === 'summary' && (
              <div>
                <h5 style={{ color: '#C084FC', fontSize: '0.88rem', fontWeight: 600, marginBottom: '8px' }}>
                  What Happened & Why it Occurs
                </h5>
                <p style={{ color: '#E8F1FF', fontSize: '0.86rem', lineHeight: '1.7', whiteSpace: 'pre-wrap' }}>
                  {explanation.explanation}
                </p>
              </div>
            )}

            {activeTab === 'impact' && (
              <div>
                <h5 style={{ color: '#FF8A1F', fontSize: '0.88rem', fontWeight: 600, marginBottom: '8px' }}>
                  Attack Vector & Business Impact
                </h5>
                <p style={{ color: '#E8F1FF', fontSize: '0.86rem', lineHeight: '1.7', whiteSpace: 'pre-wrap' }}>
                  {explanation.impact}
                </p>
              </div>
            )}

            {activeTab === 'remediation' && (
              <div>
                <h5 style={{ color: '#00E5FF', fontSize: '0.88rem', fontWeight: 600, marginBottom: '8px' }}>
                  Code-Level Fix & Verification Instructions
                </h5>
                <div 
                  className="font-mono-code"
                  style={{ 
                    background: '#040F1E', 
                    padding: '14px 16px', 
                    borderRadius: '8px', 
                    border: '1px solid #0F2F4E',
                    color: '#8AA4C8',
                    fontSize: '0.82rem',
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {explanation.remediation}
                </div>
              </div>
            )}
          </div>

          {/* Action Footer: Regenerate Button */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '18px', paddingTop: '14px', borderTop: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <span style={{ fontSize: '0.74rem', color: '#6482A6' }}>
              Generated: {new Date(explanation.created_at || Date.now()).toLocaleString()}
            </span>

            <button
              onClick={() => handleExplain(true)}
              disabled={isRegenerating}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '6px',
                background: 'rgba(139, 92, 246, 0.15)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                color: '#C084FC',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: isRegenerating ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <RefreshCw size={13} className={isRegenerating ? 'animate-spin' : ''} />
              <span>{isRegenerating ? 'Regenerating...' : 'Regenerate AI Analysis'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Error Notice */}
      {error && (
        <div style={{ marginTop: '14px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(255, 77, 94, 0.15)', border: '1px solid rgba(255, 77, 94, 0.35)', color: '#FF4D5E', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
