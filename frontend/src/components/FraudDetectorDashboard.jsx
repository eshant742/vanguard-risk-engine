import { useState } from 'react'

export default function FraudDetectorDashboard() {
  const [amount, setAmount] = useState(5000)
  const [velocity, setVelocity] = useState(1)
  const [ipMatch, setIpMatch] = useState("1")
  const [timeSince, setTimeSince] = useState(120)
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handlePredict = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/fraud/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: parseFloat(amount),
          device_velocity: parseInt(velocity),
          ip_country_match: parseInt(ipMatch),
          time_since_last_txn: parseFloat(timeSince)
        }),
      });
      
      if (!response.ok) throw new Error('API failed')
      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <div className="card">
        <h3 className="card-title">Simulate Live Transaction</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Input synthetic transaction parameters to test the ML Random Forest model.
        </p>
        
        <form onSubmit={handlePredict} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Transaction Amount (INR)</label>
            <input 
              type="number" 
              className="input-box" 
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Device Velocity (Txns past hour)</label>
            <input 
              type="number" 
              className="input-box" 
              value={velocity}
              onChange={(e) => setVelocity(e.target.value)}
              required
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>IP Country Matches Card Country</label>
            <select 
              className="input-box" 
              value={ipMatch}
              onChange={(e) => setIpMatch(e.target.value)}
              style={{ backgroundColor: 'var(--bg-lighter)' }}
            >
              <option value="1">Yes (Normal)</option>
              <option value="0">No (Mismatch)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Minutes Since Last Transaction</label>
            <input 
              type="number" 
              className="input-box" 
              value={timeSince}
              onChange={(e) => setTimeSince(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="primary-btn" 
            disabled={loading}
            style={{ marginTop: '1rem' }}
          >
            {loading ? <div className="loader"></div> : 'Run AI Fraud Prediction'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3 className="card-title">AI Prediction Output</h3>
        
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
            Submit a transaction to see the ML model's prediction.
          </div>
        )}

        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>Probability of Fraud</div>
              <div style={{ fontSize: '3rem', fontWeight: '800', color: result.is_fraud ? '#f87171' : '#4ade80' }}>
                {result.fraud_probability}%
              </div>
            </div>
            
            <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '1rem 0' }}></div>
            
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderRadius: '100px', backgroundColor: result.is_fraud ? 'rgba(248, 113, 113, 0.1)' : 'rgba(74, 222, 128, 0.1)', color: result.is_fraud ? '#f87171' : '#4ade80', width: 'fit-content', fontWeight: '600', border: `1px solid ${result.is_fraud ? '#f87171' : '#4ade80'}` }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: result.is_fraud ? '#f87171' : '#4ade80' }}></div>
              ACTION: {result.action}
            </div>

            <p style={{ color: 'var(--text-light)', lineHeight: '1.6', fontSize: '0.95rem' }}>
              {result.reason}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
