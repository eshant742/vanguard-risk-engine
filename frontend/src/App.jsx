import { useState } from 'react'
import UnderwritingDashboard from './components/UnderwritingDashboard'
import FXRiskDashboard from './components/FXRiskDashboard'

function App() {
  const [activeTab, setActiveTab] = useState('underwriting')

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <span>Vanguard</span> Risk Engine
        </div>
        
        <div style={{ marginTop: '2rem', padding: '0 1rem', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
          Risk Engines
        </div>
        
        <nav className="nav-links">
          <button 
            className={`nav-btn ${activeTab === 'underwriting' ? 'active' : ''}`}
            onClick={() => setActiveTab('underwriting')}
          >
            🏢 Merchant Underwriting
          </button>
          
          <button 
            className={`nav-btn ${activeTab === 'fxrisk' ? 'active' : ''}`}
            onClick={() => setActiveTab('fxrisk')}
          >
            🌐 FX & Liquidity Risk
          </button>
        </nav>
        
        <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(43, 108, 176, 0.1)', borderRadius: '8px', border: '1px solid rgba(43, 108, 176, 0.2)' }}>
          <div style={{ fontSize: '0.85rem', color: '#fff', fontWeight: '600' }}>AI Builder Internship 2026</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Risk Manager Track</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            {activeTab === 'underwriting' ? 'Merchant Risk Engine' : 'Macroeconomic Risk Engine'}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: '500', color: '#fff' }}>Admin User</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-green)' }}>System Online</div>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
              AD
            </div>
          </div>
        </header>

        {activeTab === 'underwriting' && <UnderwritingDashboard />}
        {activeTab === 'fxrisk' && <FXRiskDashboard />}
        
      </main>
    </div>
  )
}

export default App
