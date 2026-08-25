import { useState, useEffect } from 'react'
import { API_BASE } from '../App'

export default function MLMetricsDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/fraud/metrics`)
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
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
        {error}. Make sure the Python backend is running!
      </div>
    )
  }

  const featureNameMap = {
    'amount': 'Transaction Amount',
    'device_velocity': 'Device Velocity',
    'ip_country_match': 'IP Country Match',
    'time_since_last_txn': 'Time Since Last Txn'
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      <div className="card">
        <h3 className="card-title">Model Architecture & The Bar</h3>
        <p style={{ color: 'var(--text-main)', lineHeight: '1.6', fontSize: '0.95rem' }}>
          This ML engine was explicitly built to fulfill Razorpay's Track 02 mandate: <i>"Build a working detector... with measured precision and recall on a held-out test set, including honest metrics on false-positive cost."</i>
        </p>
        <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.9rem', marginTop: '1rem' }}>
          <strong>Algorithm:</strong> Random Forest Classifier (n_estimators=50, max_depth=5)<br/>
          <strong>Training Data:</strong> {metrics?.train_set_size?.toLocaleString()} synthetic merchant transactions<br/>
          <strong>Held-Out Test Set:</strong> {metrics?.test_set_size} transactions (20% stratified split)
        </p>
      </div>

      {/* Primary Metrics Row */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Precision</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#60a5fa', margin: '0.5rem 0' }}>
            {(metrics?.precision * 100).toFixed(1)}%
          </div>
          <div className="progress-track">
            <div className="progress-fill-cyan" style={{ width: `${metrics?.precision * 100}%` }}></div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
            When it flags fraud, it is correct {(metrics?.precision * 100).toFixed(1)}% of the time.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Recall</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#c084fc', margin: '0.5rem 0' }}>
            {(metrics?.recall * 100).toFixed(1)}%
          </div>
          <div className="progress-track">
            <div className="progress-fill-magenta" style={{ width: `${metrics?.recall * 100}%` }}></div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
            It successfully catches {(metrics?.recall * 100).toFixed(1)}% of all true fraud.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>F1 Score</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#34d399', margin: '0.5rem 0' }}>
            {(metrics?.f1_score * 100).toFixed(1)}%
          </div>
          <div className="progress-track">
            <div className="progress-fill-cyan" style={{ width: `${metrics?.f1_score * 100}%`, background: 'linear-gradient(90deg, #34d399, #059669)' }}></div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
            Harmonic mean of Precision and Recall.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>ROC-AUC</div>
          <div style={{ fontSize: '3rem', fontWeight: '800', color: '#fbbf24', margin: '0.5rem 0' }}>
            {(metrics?.roc_auc * 100).toFixed(1)}%
          </div>
          <div className="progress-track">
            <div className="progress-fill-cyan" style={{ width: `${metrics?.roc_auc * 100}%`, background: 'linear-gradient(90deg, #fbbf24, #f59e0b)' }}></div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
            Area Under the ROC Curve — class separability.
          </div>
        </div>

      </div>

      {/* Financial Impact Row */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
        
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>False-Positive Cost</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--danger)', margin: '0.5rem 0' }}>
            ₹{metrics?.false_positive_cost_inr?.toLocaleString() || 0}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Total CLV lost by falsely blocking {metrics?.false_positives} legitimate customers.
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--primary)', backgroundColor: 'var(--primary-glow)' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 'bold' }}>Net Margin Protected</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--primary)', margin: '0.5rem 0' }}>
            ₹{metrics?.net_margin_protected_inr?.toLocaleString() || 0}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', textAlign: 'center' }}>
            Fraud Prevented (₹{metrics?.total_fraud_prevented_inr?.toLocaleString() || 0}) minus False Positive Costs.
          </div>
        </div>

      </div>

      {/* Feature Importance */}
      {metrics?.feature_importance && (
        <div className="card">
          <h3 className="card-title">Feature Importance (Explainable AI)</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Random Forest feature importance scores show which input variables contribute most to the fraud prediction. This is the model's built-in explainability.
          </p>
          <div className="feature-bar-wrapper">
            {metrics.feature_importance.map((feat, idx) => (
              <div key={idx} className="feature-bar-item">
                <div className="feature-bar-label">
                  {featureNameMap[feat.feature] || feat.feature}
                </div>
                <div className="feature-bar-track">
                  <div 
                    className="feature-bar-fill" 
                    style={{ width: `${feat.importance * 100}%` }}
                  ></div>
                </div>
                <div className="feature-bar-value">
                  {(feat.importance * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confusion Matrix */}
      <div className="card">
        <h3 className="card-title">Confusion Matrix (Test Set)</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(80px, auto) 1fr 1fr', gap: '1rem', marginTop: '2rem' }}>
          <div></div>
          <div style={{ textAlign: 'center', fontWeight: '600', color: 'var(--text-main)', fontSize: '0.9rem' }}>Predicted SAFE</div>
          <div style={{ textAlign: 'center', fontWeight: '600', color: 'var(--text-main)', fontSize: '0.9rem' }}>Predicted FRAUD</div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: '600', color: 'var(--text-main)', fontSize: '0.9rem', textAlign: 'right' }}>Actual<br/>SAFE</div>
          <div style={{ backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid #4ade80', padding: '1.5rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--success)' }}>{metrics?.true_negatives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>True Negatives</div>
          </div>
          <div style={{ backgroundColor: 'var(--danger-glow)', border: '1px solid #f87171', padding: '1.5rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--danger)' }}>{metrics?.false_positives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>False Positives</div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: '600', color: 'var(--text-main)', fontSize: '0.9rem', textAlign: 'right' }}>Actual<br/>FRAUD</div>
          <div style={{ backgroundColor: 'var(--danger-glow)', border: '1px solid #f87171', padding: '1.5rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--danger)' }}>{metrics?.false_negatives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>False Negatives</div>
          </div>
          <div style={{ backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid #4ade80', padding: '1.5rem', textAlign: 'center', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--success)' }}>{metrics?.true_positives}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>True Positives</div>
          </div>
        </div>

      </div>

    </div>
  )
}
