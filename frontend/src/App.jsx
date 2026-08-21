import { useState } from 'react'
import FraudDetectorDashboard from './components/FraudDetectorDashboard'
import MLMetricsDashboard from './components/MLMetricsDashboard'
import ChargebackDashboard from './components/ChargebackDashboard'
import AbuseRingDashboard from './components/AbuseRingDashboard'
import ReturnRiskDashboard from './components/ReturnRiskDashboard'
import { ShieldAlert, BarChart3, Receipt, Users, Undo2, ChevronLeft, ChevronRight, Activity } from 'lucide-react'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('fraud')
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const getTitle = () => {
    switch(activeTab) {
      case 'fraud': return 'Transaction Fraud-Spike Detector';
      case 'metrics': return 'Model Evaluation (Held-Out Test Set)';
      case 'chargeback': return 'Chargeback Evidence Auto-Responder';
      case 'abuse': return 'Abuse-Ring Sentinel';
      case 'returnrisk': return 'Return-Risk Scorer (Wardrobing Fraud)';
      default: return 'Dashboard';
    }
  }

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
            className={`nav-btn ${activeTab === 'fraud' ? 'active' : ''}`}
            onClick={() => setActiveTab('fraud')}
            title="Live Fraud Detector"
          >
            <ShieldAlert size={20} color={activeTab === 'fraud' ? 'var(--cyber-cyan)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Live Fraud Detector</span>}
          </button>
          
          <button 
            className={`nav-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
            title="ML Metrics Evaluator"
          >
            <BarChart3 size={20} color={activeTab === 'metrics' ? 'var(--cyber-cyan)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>ML Metrics Evaluator</span>}
          </button>

          <button 
            className={`nav-btn ${activeTab === 'chargeback' ? 'active' : ''}`}
            onClick={() => setActiveTab('chargeback')}
            title="Chargeback Responder"
          >
            <Receipt size={20} color={activeTab === 'chargeback' ? 'var(--cyber-cyan)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Chargeback Responder</span>}
          </button>

          <button 
            className={`nav-btn ${activeTab === 'abuse' ? 'active' : ''}`}
            onClick={() => setActiveTab('abuse')}
            title="Abuse-Ring Sentinel"
          >
            <Users size={20} color={activeTab === 'abuse' ? 'var(--cyber-cyan)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Abuse-Ring Sentinel</span>}
          </button>

          <button 
            className={`nav-btn ${activeTab === 'returnrisk' ? 'active' : ''}`}
            onClick={() => setActiveTab('returnrisk')}
            title="Return-Risk Scorer"
          >
            <Undo2 size={20} color={activeTab === 'returnrisk' ? 'var(--cyber-cyan)' : 'var(--text-muted)'} />
            {isSidebarOpen && <span>Return-Risk Scorer</span>}
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
          <h2>{getTitle()}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: '500' }}>Admin Console</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--cyber-cyan)', display: 'flex', alignItems: 'center', gap: '0.4rem', justifyContent: 'flex-end' }}>
                <div className="live-dot"></div> System Active
              </div>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--panel-charcoal)', border: '1px solid var(--border-faint)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '600', color: 'var(--text-muted)' }}>
              AD
            </div>
          </div>
        </header>

        {/* Live Threat Ticker (Wow Factor) */}
        <div className="threat-ticker-wrapper">
          <div className="ticker-label">
            <Activity size={16} color="var(--electric-magenta)" />
            LIVE STREAM
          </div>
          <div className="ticker-content">
            <div className="ticker-item">[14:02:11] Blocked Velocity Attack from <span className="highlight">103.44.21.99</span> (Saved ₹14,500)</div>
            <div className="ticker-item">[14:02:44] AVS Mismatch on <span className="highlight">pay_9xL21M</span> (Action: Warning Issued)</div>
            <div className="ticker-item">[14:03:02] Wardrobing Fraud Prevented - User <span className="highlight">CUST-881</span> (Saved ₹4,200)</div>
            <div className="ticker-item">[14:03:15] Abuse-Ring <span className="highlight">RNG-8472</span> Neutered - 7 Cards Banned</div>
            <div className="ticker-item">[14:04:10] Defeated Chargeback Claim on <span className="highlight">pay_P41kL</span></div>
            <div className="ticker-item">[14:04:22] Blocked Velocity Attack from <span className="highlight">103.44.21.99</span> (Saved ₹14,500)</div>
          </div>
        </div>

        <div className="dashboard-content">
          {activeTab === 'fraud' && <FraudDetectorDashboard />}
          {activeTab === 'metrics' && <MLMetricsDashboard />}
          {activeTab === 'chargeback' && <ChargebackDashboard />}
          {activeTab === 'abuse' && <AbuseRingDashboard />}
          {activeTab === 'returnrisk' && <ReturnRiskDashboard />}
        </div>
      </main>
    </div>
  )
}

export default App
