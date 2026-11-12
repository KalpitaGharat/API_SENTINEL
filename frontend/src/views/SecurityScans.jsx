import React, { useState, useEffect } from 'react';
import { Play, Clock } from 'lucide-react';
import NewSecurityScan from './NewSecurityScan';
import ScanHistory from './ScanHistory';
import ErrorBoundary from '../components/ErrorBoundary';

function SecurityScansContent({ setActivePage, initialTab = 'new', initialTargetId }) {
  const [activeTab, setActiveTab] = useState(initialTab);

  // Sync if initialTab prop changes
  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Sub-navigation Tabs */}
      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px', 
          borderBottom: '1px solid #0F2F4E', 
          paddingBottom: '12px' 
        }}
      >
        <button
          onClick={() => setActiveTab('new')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 18px',
            borderRadius: '8px',
            background: activeTab === 'new' 
              ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(2, 132, 199, 0.2) 100%)' 
              : 'transparent',
            border: activeTab === 'new' ? '1px solid #00E5FF' : '1px solid #0F2F4E',
            color: activeTab === 'new' ? '#00E5FF' : '#8AA4C8',
            fontSize: '0.86rem',
            fontWeight: activeTab === 'new' ? 700 : 500,
            cursor: 'pointer',
            transition: 'all 0.18s ease',
            boxShadow: activeTab === 'new' ? '0 0 14px rgba(0, 229, 255, 0.25)' : 'none',
          }}
        >
          <Play size={15} />
          <span>Launch New Scan</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 18px',
            borderRadius: '8px',
            background: activeTab === 'history' 
              ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(2, 132, 199, 0.2) 100%)' 
              : 'transparent',
            border: activeTab === 'history' ? '1px solid #00E5FF' : '1px solid #0F2F4E',
            color: activeTab === 'history' ? '#00E5FF' : '#8AA4C8',
            fontSize: '0.86rem',
            fontWeight: activeTab === 'history' ? 700 : 500,
            cursor: 'pointer',
            transition: 'all 0.18s ease',
            boxShadow: activeTab === 'history' ? '0 0 14px rgba(0, 229, 255, 0.25)' : 'none',
          }}
        >
          <Clock size={15} />
          <span>Historical Scan Registry</span>
        </button>
      </div>

      {/* Render Active Sub-View */}
      {activeTab === 'new' ? (
        <NewSecurityScan setActivePage={setActivePage} initialTargetId={initialTargetId} />
      ) : (
        <ScanHistory setActivePage={setActivePage} />
      )}
    </div>
  );
}

export default function SecurityScans(props) {
  return (
    <ErrorBoundary title="Security Scans Intercepted">
      <SecurityScansContent {...props} />
    </ErrorBoundary>
  );
}
