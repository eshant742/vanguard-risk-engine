import { useState } from 'react'
import { Copy, Check, AlertTriangle } from 'lucide-react'
import { API_BASE } from '../App'

export default function ChargebackDashboard() {
  const [txnId, setTxnId] = useState('pay_Q8V9xwM3nKdL')
  const [claim, setClaim] = useState('I never received this item. Tracking is fake.')
  const [loading, setLoading] = useState(false)
  const [evidence, setEvidence] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleGenerate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setEvidence(null)
    setCopied(false)
    
    try {
      const response = await fetch(`${API_BASE}/api/fraud/chargeback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txnId,
          customer_claim: claim
        })
      })
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `API returned ${response.status}`)
      }
      const data = await response.json()
      setEvidence(data.evidence_letter)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(evidence)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea')
      textarea.value = evidence
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="dashboard-grid">
      
      <div className="card" style={{ height: 'fit-content' }}>
        <h3 className="card-title">Chargeback Input</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Paste the customer's dispute claim. The AI will cross-reference internal logs to generate an evidence defense letter.
        </p>

        <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label className="input-label">Transaction ID</label>
            <input 
              type="text" 
              className="input-box" 
              value={txnId}
              onChange={(e) => setTxnId(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label className="input-label">Customer Dispute Reason</label>
            <textarea 
              className="input-box" 
              style={{ minHeight: '100px', resize: 'vertical' }}
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="primary-btn" 
            disabled={loading}
            style={{ marginTop: '1rem' }}
          >
            {loading ? <div className="loader"></div> : 'Generate Evidence Letter'}
          </button>
        </form>
      </div>

      <div className="card" style={{ minHeight: '600px', backgroundColor: '#1a1d24' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title" style={{ marginBottom: 0 }}>Generated Visa/Mastercard Defense Letter</h3>
          {evidence && (
            <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy}>
              {copied ? <><Check size={14} /> Copied!</> : <><Copy size={14} /> Copy</>}
            </button>
          )}
        </div>
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
          </div>
        )}

        {error && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
            {error}. Make sure the Python backend is running!
          </div>
        )}

        {!loading && !evidence && !error && (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Enter a dispute claim to automatically generate a formal chargeback evidence response.
          </div>
        )}

        {evidence && (
          <div style={{ 
            marginTop: '1.5rem', 
            padding: '1.5rem', 
            backgroundColor: '#0f1115', 
            borderRadius: '8px',
            border: '1px solid var(--border-light)',
            fontFamily: "'JetBrains Mono', monospace",
            whiteSpace: 'pre-wrap',
            color: '#e2e8f0',
            fontSize: '0.85rem',
            lineHeight: '1.6',
            overflowY: 'auto',
            maxHeight: '500px'
          }}>
            {evidence}
          </div>
        )}

        {evidence && result && result.nlp_confidence !== undefined && (
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ backgroundColor: 'rgba(255,255,255,0.05)', padding: '0.3rem 0.6rem', borderRadius: '4px' }}>
                NLP Model: <span style={{ color: 'var(--primary)' }}>TF-IDF + Cosine Similarity</span>
              </span>
              <span style={{ backgroundColor: 'rgba(255,255,255,0.05)', padding: '0.3rem 0.6rem', borderRadius: '4px' }}>
                Confidence: <span style={{ color: result.nlp_confidence > 50 ? 'var(--success)' : 'var(--danger)' }}>{result.nlp_confidence}%</span>
              </span>
              {result.low_confidence && (
                <span style={{ backgroundColor: 'var(--danger-glow)', color: 'var(--danger)', border: '1px solid var(--danger)', padding: '0.3rem 0.6rem', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <AlertTriangle size={14} /> LOW CONFIDENCE — MANUAL REVIEW RECOMMENDED
                </span>
              )}
            </div>

            {/* NLP Scores Breakdown */}
            {result.nlp_scores && Object.keys(result.nlp_scores).length > 0 && (
              <div style={{ backgroundColor: 'var(--surface-input)', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 'bold', marginBottom: '0.75rem' }}>NLP Category Scores</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
                  {Object.entries(result.nlp_scores)
                    .sort((a, b) => b[1] - a[1]) // Sort descending by score
                    .map(([cat, score]) => (
                      <div key={cat} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-main)' }}>
                        <span style={{ textTransform: 'capitalize' }}>{cat.replace('_', ' ')}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, marginLeft: '2rem' }}>
                          <div style={{ flex: 1, height: '6px', backgroundColor: 'var(--bg-main)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${score * 100}%`, height: '100%', backgroundColor: score * 100 === result.nlp_confidence ? 'var(--primary)' : 'var(--border-light)', transition: 'width 0.5s ease-out' }}></div>
                          </div>
                          <span style={{ width: '45px', textAlign: 'right', fontWeight: score * 100 === result.nlp_confidence ? '600' : 'normal', color: score * 100 === result.nlp_confidence ? 'var(--primary)' : 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                            {(score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  )
}
