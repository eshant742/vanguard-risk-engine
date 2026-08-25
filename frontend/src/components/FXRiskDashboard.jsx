import { useState, useEffect } from 'react'
import { API_BASE } from '../App'

export default function FXRiskDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState('')

  const fetchData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/fx-risk`)
      if (!response.ok) throw new Error(`API returned ${response.status}`)
      const result = await response.json()
      setData(result)
      setError(null)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto refresh every 30 seconds to simulate real-time dashboard
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
        {error}. Make sure the Python backend is running!
      </div>
    )
  }

  if (!data) return null

  const getStatusColorVar = (color) => {
    switch(color) {
      case 'green': return 'var(--primary)'
      case 'yellow': return 'var(--warning)'
      case 'red': return 'var(--danger)'
      default: return 'var(--text-muted)'
    }
  }

  const getStatusBgVar = (color) => {
    switch(color) {
      case 'green': return 'var(--primary-glow)'
      case 'yellow': return 'var(--warning-glow)'
      case 'red': return 'var(--danger-glow)'
      default: return 'transparent'
    }
  }

  return (
    <div>
      {/* Status header — no duplicate <h2> since topbar already has title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <p className="subtitle">Real-time global currency monitoring and sentiment-based risk prediction.</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>System Risk Level</div>
          <span className="badge" style={{ 
            fontSize: '1rem', 
            padding: '0.5rem 1rem',
            background: getStatusBgVar(data.status_color),
            color: getStatusColorVar(data.status_color),
            border: `1px solid ${getStatusColorVar(data.status_color)}`
          }}>
            <span className="pulse-indicator" style={{ backgroundColor: getStatusColorVar(data.status_color) }}>
              <span style={{ display: 'none' }}></span>
            </span>
            {data.system_status}
          </span>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>Last updated: {lastUpdated}</div>
        </div>
      </div>

      {/* FX Rate Ticker */}
      <div className="animate-fade-in stagger-1" style={{ background: 'var(--surface-input)', padding: '1rem 1.5rem', borderRadius: '12px', border: '1px solid var(--border-light)', display: 'flex', gap: '2.5rem', overflowX: 'auto', marginBottom: '2rem' }}>
        {Object.entries(data.rates).map(([currency, rate]) => (
          <div key={currency} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>{data.base_currency} / {currency}</span>
            <span style={{ fontSize: '1.3rem', fontWeight: 'bold', color: 'var(--primary)', fontFamily: "'JetBrains Mono', monospace" }}>{(Number(rate) || 0).toFixed(2)}</span>
          </div>
        ))}
      </div>

      <div className="dashboard-grid animate-fade-in stagger-2">
        {/* Settlement Risk Score Card */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', paddingBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: 'var(--text-heading)', textTransform: 'uppercase', letterSpacing: '1.5px', fontSize: '0.95rem' }}>Settlement Risk Score</h3>
            <div style={{ 
              fontSize: '3.5rem', 
              fontWeight: '800', 
              lineHeight: 1,
              color: getStatusColorVar(data.status_color),
              textShadow: `0 0 20px ${getStatusBgVar(data.status_color)}`
            }}>
              {data.macro_risk_score}
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Score is calculated by blending real-time FX volatility with live NLP sentiment analysis of global financial news. 
            Scores &gt; 75 trigger automated spread widening.
          </p>
          
          <div style={{ marginTop: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span>0 (Stable)</span>
              <span>100 (Critical)</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div 
                style={{ 
                  width: `${data.macro_risk_score}%`, 
                  height: '100%', 
                  background: getStatusColorVar(data.status_color),
                  transition: 'width 1s ease-in-out',
                  boxShadow: `0 0 10px ${getStatusBgVar(data.status_color)}`
                }}
              ></div>
            </div>
          </div>

          {/* Average sentiment */}
          {data.average_sentiment !== undefined && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface-input)', borderRadius: '8px', border: '1px solid var(--border-light)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Avg News Sentiment</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '700', color: getStatusColorVar(data.average_sentiment > 0.1 ? 'green' : data.average_sentiment < -0.1 ? 'red' : 'yellow'), fontFamily: "'JetBrains Mono', monospace" }}>
                  {data.average_sentiment > 0 ? '+' : ''}{data.average_sentiment.toFixed(2)}
                </div>
              </div>
              
              {data.volatility_metrics && (
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>7-Day Volatility (INR)</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary)', fontFamily: "'JetBrains Mono', monospace" }}>
                    {data.volatility_metrics.inr_volatility.toFixed(4)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* News Sentiment Card */}
        <div className="card">
          <h3 className="card-title">Live AI News Sentiment (RSS)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {data.news.map((item, index) => (
              <div key={index} className="animate-fade-in" style={{ 
                animationDelay: `${index * 0.1}s`, 
                padding: '1rem', 
                borderLeft: `3px solid ${getStatusColorVar(item.color)}`,
                background: 'var(--surface-input)', 
                borderRadius: '0 8px 8px 0' 
              }}>
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '500', marginBottom: '0.5rem', color: 'var(--text-main)' }}>{item.headline}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>VADER Sentiment Score</span>
                    <span style={{ color: getStatusColorVar(item.color), fontWeight: 'bold', fontFamily: "'JetBrains Mono', monospace" }}>{item.sentiment.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
