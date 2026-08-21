import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { API_BASE } from '../App'

export default function ChargebackDashboard() {
  const [txnId, setTxnId] = useState('pay_Q8V9xwM3nKdL')
  const [claim, setClaim] = useState('I never received this item. Tracking is fake.')
  const [loading, setLoading] = useState(false)
  const [evidence, setEvidence] = useState(null)
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
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Transaction ID</label>
            <input 
              type="text" 
              className="input-box" 
              value={txnId}
              onChange={(e) => setTxnId(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Customer Dispute Reason</label>
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
          <div style={{ padding: '2rem', textAlign: 'center', color: '#f87171' }}>
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
            border: '1px solid var(--border-color)',
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
      </div>

    </div>
  )
}
