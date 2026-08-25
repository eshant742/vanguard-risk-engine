import { useState, useEffect } from 'react'
import FraudDetectorDashboard from './components/FraudDetectorDashboard'
import MLMetricsDashboard from './components/MLMetricsDashboard'
import ChargebackDashboard from './components/ChargebackDashboard'
import AbuseRingDashboard from './components/AbuseRingDashboard'
import ReturnRiskDashboard from './components/ReturnRiskDashboard'
import FXRiskDashboard from './components/FXRiskDashboard'
import UnderwritingDashboard from './components/UnderwritingDashboard'
import { ShieldAlert, BarChart3, Receipt, Users, Undo2, ChevronLeft, ChevronRight, Activity, Globe, FileText } from 'lucide-react'
import './index.css'

// Single source of truth for API URL
export const API_BASE = 'http://localhost:8000'

import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
          <h2>UI Render Error</h2>
          <p>{this.state.error?.message || "Something went wrong rendering this module."}</p>
          <button className="primary-btn" onClick={() => this.setState({ hasError: false })} style={{ marginTop: '1rem' }}>Try Again</button>
        </div>
      )
    }
    return this.props.children
  }
}

/**
 * Safe text highlighting — replaces dangerouslySetInnerHTML.
 * Splits text on known patterns and wraps matches in styled spans.
 */
function HighlightedText({ text }) {
  const pattern = /(₹[\d,]+|pay_\w+|CUST-\d+|RNG-\d+|[\d]+\.[\d]+\.[\d]+\.[\d]+)/g
  const parts = text.split(pattern)
  
  // When using split with a capturing group, matched segments appear at odd indices
  return (
    <>
      {parts.map((part, i) => 
        i % 2 === 1
          ? <span key={i} className="highlight">{part}</span>
          : <span key={i}>{part}</span>
      )}
    </>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState('fraud')
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [tickerEvents, setTickerEvents] = useState([])
  const [tabKey, setTabKey] = useState(0)

  // Fetch live activity feed for the ticker
  useEffect(() => {
    const fetchTicker = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/fraud/activity-feed`)
        const data = await res.json()
        setTickerEvents(data.events || [])
      } catch {
        // Fallback static events if backend is not running
        setTickerEvents([
          { timestamp: "14:02:11", message: "Blocked Velocity Attack from 103.44.21.99 (Saved ₹14,500)" },
          { timestamp: "14:02:44", message: "AVS Mismatch on pay_9xL21M (Action: Warning Issued)" },
          { timestamp: "14:03:02", message: "Wardrobing Fraud Prevented - User CUST-881 (Saved ₹4,200)" },
          { timestamp: "14:03:15", message: "Abuse-Ring RNG-8472 Neutered - 7 Cards Banned" },
          { timestamp: "14:04:10", message: "Defeated Chargeback Claim on pay_P41kL" },
        ])
      }
    }
    fetchTicker()
    // Refresh ticker every 30 seconds
    const interval = setInterval(fetchTicker, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setTabKey(prev => prev + 1)
  }

  const getTitle = () => {
    switch(activeTab) {
      case 'fraud': return 'Transaction Fraud-Spike Detector';
      case 'metrics': return 'Model Evaluation (Held-Out Test Set)';
      case 'chargeback': return 'Chargeback Evidence Auto-Responder';
      case 'abuse': return 'Abuse-Ring Sentinel';
      case 'returnrisk': return 'Return-Risk Scorer (Wardrobing Fraud)';
      case 'underwrite': return 'AI Merchant Underwriting';
      case 'fx': return 'Macroeconomic FX & Liquidity Risk';
      default: return 'Dashboard';
    }
  }

  // Build ticker items — duplicate for seamless scrolling
  const tickerItems = tickerEvents.length > 0
    ? tickerEvents.map((e, i) => `[${e.timestamp}] ${e.message}`)
    : []
  // Duplicate the array for seamless loop
  const allTickerItems = [...tickerItems, ...tickerItems]

  return (
    <div className="app-container">
      {/* Floating Left Dock (Slider) */}
      <aside className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {isSidebarOpen && (
            <div className="brand">
              <span>VAN</span>GUARD
            </div>
          )}
          <button className="slider-toggle-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            {isSidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>
        
        {isSidebarOpen && (
          <div style={{ marginTop: '1.5rem', padding: '0 0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontFamily: "'JetBrains Mono', monospace" }}>
            Modules
          </div>
        )}
        
        <nav className="nav-links" style={{ marginTop: isSidebarOpen ? '0' : '2rem' }}>
          <button 
            id="nav-fraud-detector"
            className={`nav-btn ${activeTab === 'fraud' ? 'active' : ''}`}
            onClick={() => handleTabChange('fraud')}
            title="Live Fraud Detector"
          >
            <ShieldAlert size={20} color={activeTab === 'fraud' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Live Fraud Detector</span>}
          </button>
          
          <button 
            id="nav-ml-metrics"
            className={`nav-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => handleTabChange('metrics')}
            title="ML Metrics Evaluator"
          >
            <BarChart3 size={20} color={activeTab === 'metrics' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>ML Metrics Evaluator</span>}
          </button>

          <button 
            id="nav-chargeback"
            className={`nav-btn ${activeTab === 'chargeback' ? 'active' : ''}`}
            onClick={() => handleTabChange('chargeback')}
            title="Chargeback Responder"
          >
            <Receipt size={20} color={activeTab === 'chargeback' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Chargeback Responder</span>}
          </button>

          <button 
            id="nav-abuse-ring"
            className={`nav-btn ${activeTab === 'abuse' ? 'active' : ''}`}
            onClick={() => handleTabChange('abuse')}
            title="Abuse-Ring Sentinel"
          >
            <Users size={20} color={activeTab === 'abuse' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Abuse-Ring Sentinel</span>}
          </button>

          <button 
            id="nav-return-risk"
            className={`nav-btn ${activeTab === 'returnrisk' ? 'active' : ''}`}
            onClick={() => handleTabChange('returnrisk')}
            title="Return-Risk Scorer"
          >
            <Undo2 size={20} color={activeTab === 'returnrisk' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Return-Risk Scorer</span>}
          </button>

          <button 
            id="nav-underwriting"
            className={`nav-btn ${activeTab === 'underwrite' ? 'active' : ''}`}
            onClick={() => handleTabChange('underwrite')}
            title="AI Underwriting"
          >
            <FileText size={20} color={activeTab === 'underwrite' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>AI Underwriting</span>}
          </button>
          
          <button 
            id="nav-fx-risk"
            className={`nav-btn ${activeTab === 'fx' ? 'active' : ''}`}
            onClick={() => handleTabChange('fx')}
            title="FX Risk Engine"
          >
            <Globe size={20} color={activeTab === 'fx' ? 'var(--primary)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>FX Risk Engine</span>}
          </button>
        </nav>

        {isSidebarOpen && (
          <div className="sidebar-footer">
            <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', fontWeight: '600', fontFamily: "'JetBrains Mono', monospace" }}>Razorpay Buildathon</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Track 02: Risk Manager</div>
          </div>
        )}
      </aside>

      {/* Main Content Canvas */}
      <main className="main-content">
        <header className="topbar">
          <div style={{display: "flex", flexDirection: "column"}}><span className="eyebrow">ACTIVE MODULE</span><h2>{getTitle()}</h2></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: '500' }}>Admin Console</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.4rem', justifyContent: 'flex-end' }}>
                <div className="live-dot"></div> System Active
              </div>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--surface-input)', border: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '600', color: 'var(--text-muted)' }}>
              AD
            </div>
          </div>
        </header>

        {/* Live Threat Ticker — connected to backend */}
        <div className="threat-ticker-wrapper">
          <div className="ticker-label">
            <Activity size={16} color="var(--danger)" />
            LIVE STREAM
          </div>
          <div className="ticker-content">
            {allTickerItems.map((item, idx) => (
              <div key={idx} className="ticker-item">
                <HighlightedText text={item} />
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-content">
          <ErrorBoundary>
            <div key={tabKey} className="dashboard-view-enter">
              {activeTab === 'fraud' && <FraudDetectorDashboard />}
              {activeTab === 'metrics' && <MLMetricsDashboard />}
              {activeTab === 'chargeback' && <ChargebackDashboard />}
              {activeTab === 'abuse' && <AbuseRingDashboard />}
              {activeTab === 'returnrisk' && <ReturnRiskDashboard />}
              {activeTab === 'underwrite' && <UnderwritingDashboard />}
              {activeTab === 'fx' && <FXRiskDashboard />}
            </div>
          </ErrorBoundary>
        </div>
      </main>
    </div>
  )
}

export default App
