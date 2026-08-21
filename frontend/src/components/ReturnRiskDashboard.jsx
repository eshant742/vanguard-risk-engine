import { useState } from 'react'
import { API_BASE } from '../App'

export default function ReturnRiskDashboard() {
  const [itemsKept, setItemsKept] = useState(2)
  const [itemsReturned, setItemsReturned] = useState(8)
  const [cartValue, setCartValue] = useState(12500)
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleScore = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    
    try {
      const response = await fetch(`${API_BASE}/api/fraud/return-risk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: "CUST-991A",
          items_kept_last_year: parseInt(itemsKept),
          items_returned_last_year: parseInt(itemsReturned),
          current_cart_value: parseFloat(cartValue)
        }),
      });
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `API returned ${response.status}`)
      }
      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level) => {
    switch(level) {
      case 'CRITICAL': return '#f87171'
      case 'MEDIUM': return '#d69e2e'
      case 'LOW': return '#4ade80'
      default: return '#fff'
    }
  }

  const getRiskBg = (level) => {
    switch(level) {
      case 'CRITICAL': return 'rgba(248, 113, 113, 0.1)'
      case 'MEDIUM': return 'rgba(214, 158, 46, 0.1)'
      case 'LOW': return 'rgba(74, 222, 128, 0.1)'
      default: return 'transparent'
    }
  }

  return (
    <div className="dashboard-grid">
      <div className="card" style={{ height: 'fit-content' }}>
        <h3 className="card-title">Wardrobing Fraud Simulator</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Input a customer's historical purchase behavior. The AI calculates the probability of a return and adjusts checkout policies dynamically.
        </p>
        
        <form onSubmit={handleScore} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Items Kept (Last 12 Months)</label>
            <input 
              type="number" 
              className="input-box" 
              value={itemsKept}
              onChange={(e) => setItemsKept(e.target.value)}
              min="0"
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Items Returned (Last 12 Months)</label>
            <input 
              type="number" 
              className="input-box" 
              value={itemsReturned}
              onChange={(e) => setItemsReturned(e.target.value)}
              min="0"
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Current Cart Value (INR)</label>
            <input 
              type="number" 
              className="input-box" 
              value={cartValue}
              onChange={(e) => setCartValue(e.target.value)}
              min="0"
              step="any"
              required
            />
          </div>

          <button 
            type="submit" 
            className="primary-btn" 
            disabled={loading}
            style={{ marginTop: '1rem' }}
          >
            {loading ? <div className="loader"></div> : 'Score Return Risk'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3 className="card-title">AI Policy Recommendation</h3>
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
            <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
          </div>
        )}

        {error && (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#f87171' }}>
            {error}. Make sure the Python backend is running!
          </div>
        )}

        {!loading && !result && !error && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Submit a customer profile to generate a dynamic return policy.
          </div>
        )}

        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>Probability of Return</div>
              <div style={{ fontSize: '3rem', fontWeight: '800', color: getRiskColor(result.risk_level) }}>
                {result.return_probability}%
              </div>
            </div>

            {/* Visual risk gauge */}
            <div className="risk-gauge-wrapper">
              <div className="risk-gauge-bar">
                <div 
                  className="risk-gauge-marker" 
                  style={{ left: `${Math.min(result.return_probability, 100)}%` }}
                ></div>
              </div>
              <div className="risk-gauge-labels">
                <span>0% Low</span>
                <span>40% Medium</span>
                <span>75% Critical</span>
                <span>100%</span>
              </div>
            </div>
            
            <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '0.5rem 0' }}></div>
            
            <div style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '0.5rem', 
              padding: '0.5rem 1rem', 
              borderRadius: '100px', 
              backgroundColor: getRiskBg(result.risk_level), 
              color: getRiskColor(result.risk_level), 
              width: 'fit-content', 
              fontWeight: '600', 
              border: `1px solid ${getRiskColor(result.risk_level)}` 
            }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: getRiskColor(result.risk_level) }}></div>
              DYNAMIC ACTION: {result.action}
            </div>

            <p style={{ color: 'var(--text-light)', lineHeight: '1.6', fontSize: '0.95rem' }}>
              {result.recommendation}
            </p>

            {/* Risk Breakdown */}
            {result.breakdown && (
              <div style={{ backgroundColor: 'var(--panel-charcoal)', border: '1px solid var(--border-faint)', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--cyber-cyan)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.75rem', fontWeight: 'bold' }}>Risk Breakdown</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-light)' }}>
                    <span>Historical Return Rate</span>
                    <span style={{ color: getRiskColor(result.risk_level), fontWeight: '600' }}>{result.breakdown.return_rate}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-light)' }}>
                    <span>History Risk Factor</span>
                    <span style={{ fontWeight: '600', fontFamily: "'JetBrains Mono', monospace" }}>{result.breakdown.history_factor}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-light)' }}>
                    <span>Cart Value Risk Factor</span>
                    <span style={{ fontWeight: '600', fontFamily: "'JetBrains Mono', monospace" }}>+{result.breakdown.cart_risk_factor}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
