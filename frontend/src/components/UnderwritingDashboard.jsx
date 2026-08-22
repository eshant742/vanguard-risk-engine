import { useState } from 'react'
import { ShieldCheck, AlertOctagon, Info, ShieldAlert } from 'lucide-react'
import { API_BASE } from '../App'

export default function UnderwritingDashboard() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const analyzeUrl = async (e) => {
    e.preventDefault()
    if (!url) return
    
    setLoading(true)
    setResult(null)
    try {
      const response = await fetch(`${API_BASE}/api/underwrite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `API returned ${response.status}`)
      }
      
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error(error)
      setResult({
        status: "ERROR",
        trust_score: 0,
        action_color: "red",
        summary: "Failed to connect to backend AI engine. Make sure the Python backend is running."
      })
    }
    setLoading(false)
  }

  const getColorVar = (actionColor) => {
    switch(actionColor) {
      case 'red': return 'var(--electric-magenta)'
      case 'yellow': return 'var(--neon-amber)'
      case 'green': return 'var(--cyber-cyan)'
      default: return 'var(--text-muted)'
    }
  }

  const getBgVar = (actionColor) => {
    switch(actionColor) {
      case 'red': return 'var(--electric-magenta-glow)'
      case 'yellow': return 'var(--neon-amber-glow)'
      case 'green': return 'var(--cyber-cyan-glow)'
      default: return 'transparent'
    }
  }

  return (
    <div>
      {/* No duplicate h2 — topbar already shows the title */}
      <p className="subtitle" style={{ marginBottom: '1.5rem' }}>AI-powered risk profiling & compliance check for merchant onboarding.</p>

      <div className="card animate-scale-in">
        <h3 className="card-title">Submit New Merchant</h3>
        <form onSubmit={analyzeUrl} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <input 
            type="text" 
            id="underwrite-url-input"
            className="input-box" 
            placeholder="Enter merchant website URL (e.g., https://example.com)" 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button type="submit" id="underwrite-submit-btn" className="primary-btn" disabled={loading}>
            {loading ? <div className="loader"></div> : 'Run AI Analysis'}
          </button>
        </form>

        {result && (
          <div className="card animate-fade-in stagger-1" style={{ marginTop: '2rem', borderTop: `4px solid ${getColorVar(result.action_color)}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-faint)', paddingBottom: '1.5rem' }}>
              <div>
                <h3 className="card-title" style={{ marginBottom: '0.2rem' }}>
                  {result.trust_score >= 70 ? <ShieldCheck color="var(--cyber-cyan)" /> : <ShieldAlert color="var(--electric-magenta)" />}
                  AI Risk Report
                </h3>
                <p style={{ color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.85rem' }}>{result.url}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  fontSize: '3.5rem', 
                  fontWeight: '800', 
                  lineHeight: '1', 
                  color: getColorVar(result.action_color),
                  textShadow: `0 0 20px ${getBgVar(result.action_color)}`
                }}>
                  {result.trust_score}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Trust Score</div>
              </div>
            </div>

            {/* Trust Score Progress Bar */}
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <span>0 (Reject)</span>
                <span>40</span>
                <span>70</span>
                <span>100 (Approve)</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ 
                  width: `${result.trust_score}%`, 
                  height: '100%', 
                  background: getColorVar(result.action_color),
                  transition: 'width 1s ease-in-out',
                  boxShadow: `0 0 10px ${getBgVar(result.action_color)}`
                }}></div>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '0.5rem', 
                padding: '0.5rem 1rem', 
                borderRadius: '100px', 
                backgroundColor: getBgVar(result.action_color),
                color: getColorVar(result.action_color),
                fontWeight: '600',
                border: `1px solid ${getColorVar(result.action_color)}`
              }}>
                <div className="live-dot" style={{ backgroundColor: getColorVar(result.action_color) }}></div>
                ACTION: {result.status}
              </div>

              {/* Sentiment Score */}
              {result.flags?.sentiment_compound !== undefined && (
                <div style={{ 
                  fontSize: '0.85rem', 
                  color: 'var(--text-muted)',
                  fontFamily: "'JetBrains Mono', monospace"
                }}>
                  Sentiment: <span style={{ 
                    color: result.flags.sentiment_compound > 0.1 ? 'var(--cyber-cyan)' : result.flags.sentiment_compound < -0.1 ? 'var(--electric-magenta)' : 'var(--neon-amber)',
                    fontWeight: '600'
                  }}>
                    {result.flags.sentiment_compound > 0 ? '+' : ''}{result.flags.sentiment_compound}
                  </span>
                </div>
              )}
            </div>

            <p style={{ fontSize: '1.05rem', color: 'var(--text-light)', lineHeight: '1.6', marginBottom: '2rem' }}>
              {result.summary}
            </p>

            {result.flags && (
              <div className="dashboard-grid animate-fade-in stagger-2">
                {result.flags.prohibited_items && result.flags.prohibited_items.length > 0 && (
                  <div className="card" style={{ padding: '1.5rem', border: '1px solid var(--electric-magenta)' }}>
                    <h4 style={{ color: 'var(--electric-magenta)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      <AlertOctagon size={18} /> Prohibited Items Found
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {result.flags.prohibited_items.map((item, i) => (
                        <span key={i} style={{ background: 'var(--electric-magenta-glow)', color: 'var(--electric-magenta)', padding: '0.3rem 0.8rem', borderRadius: '4px', fontSize: '0.85rem', border: '1px solid rgba(255,42,133,0.3)', fontFamily: "'JetBrains Mono', monospace" }}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {result.flags.high_risk_items && result.flags.high_risk_items.length > 0 && (
                  <div className="card" style={{ padding: '1.5rem', border: '1px solid var(--neon-amber)' }}>
                    <h4 style={{ color: 'var(--neon-amber)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      <Info size={18} /> High-Risk Terms Found
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {result.flags.high_risk_items.map((item, i) => (
                        <span key={i} style={{ background: 'var(--neon-amber-glow)', color: 'var(--neon-amber)', padding: '0.3rem 0.8rem', borderRadius: '4px', fontSize: '0.85rem', border: '1px solid rgba(255,176,32,0.3)', fontFamily: "'JetBrains Mono', monospace" }}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Show clean report when nothing flagged */}
                {(!result.flags.prohibited_items || result.flags.prohibited_items.length === 0) && 
                 (!result.flags.high_risk_items || result.flags.high_risk_items.length === 0) && (
                  <div className="card" style={{ padding: '1.5rem', border: '1px solid var(--cyber-cyan)' }}>
                    <h4 style={{ color: 'var(--cyber-cyan)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      <ShieldCheck size={18} /> Clean Report
                    </h4>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                      No prohibited or high-risk terms detected. This merchant passes automated compliance screening.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
