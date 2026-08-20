import { useState, useEffect } from 'react'

export default function MLMetricsDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/fraud/metrics')
        if (!response.ok) throw new Error('Failed to fetch ML metrics from backend')
        const data = await response.json()
        setMetrics(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#f87171' }}>
        {error}. Make sure the Python backend is running!
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      <div className="card">
        <h3 className="card-title">Model Architecture & The Bar</h3>
        <p style={{ color: 'var(--text-light)', lineHeight: '1.6', fontSize: '0.95rem' }}>
          This ML engine was explicitly built to fulfill Razorpay's Track 02 mandate: <i>"Build a working detector... with measured precision and recall on a held-out test set, including honest metrics on false-positive cost."</i>
        </p>
        <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.9rem', marginTop: '1rem' }}>
          <strong>Algorithm:</strong> Random Forest Classifier (n_estimators=50)<br/>
          <strong>Training Data:</strong> 2,000 synthetic merchant transactions<br/>
          <strong>Held-Out Test Set:</strong> {metrics?.test_set_size} transactions (20% split)
        </p>
      </div>

      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
        
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Precision</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#60a5fa', margin: '0.5rem 0' }}>
            {(metrics?.precision * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            When it flags fraud, it is correct {(metrics?.precision * 100).toFixed(1)}% of the time.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Recall</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#c084fc', margin: '0.5rem 0' }}>
            {(metrics?.recall * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            It successfully catches {(metrics?.recall * 100).toFixed(1)}% of all true fraud.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>False-Positive Cost</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#f87171', margin: '0.5rem 0' }}>
            ₹{metrics?.false_positive_cost_inr.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Total CLV lost by falsely blocking {metrics?.false_positives} legitimate customers.
          </div>
        </div>

      </div>

      <div className="card">
        <h3 className="card-title">Confusion Matrix (Test Set)</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr 1fr', gap: '1rem', marginTop: '2rem' }}>
          <div></div>
          <div style={{ textAlign: 'center', fontWeight: '600', color: 'var(--text-light)' }}>Predicted SAFE</div>
          <div style={{ textAlign: 'center', fontWeight: '600', color: 'var(--text-light)' }}>Predicted FRAUD</div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: '600', color: 'var(--text-light)' }}>Actual SAFE</div>
          <div style={{ backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid #4ade80', padding: '2rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: '#4ade80' }}>{metrics?.true_negatives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>True Negatives</div>
          </div>
          <div style={{ backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid #f87171', padding: '2rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: '#f87171' }}>{metrics?.false_positives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>False Positives</div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: '600', color: 'var(--text-light)' }}>Actual FRAUD</div>
          <div style={{ backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid #f87171', padding: '2rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: '#f87171' }}>{metrics?.false_negatives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>False Negatives</div>
          </div>
          <div style={{ backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid #4ade80', padding: '2rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: '#4ade80' }}>{metrics?.true_positives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>True Positives</div>
          </div>
        </div>

      </div>

    </div>
  )
}
