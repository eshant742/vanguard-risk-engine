import { useState, useEffect } from 'react'

export default function AbuseRingDashboard() {
  const [rings, setRings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchRings = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/fraud/abuse-ring')
        if (!response.ok) throw new Error('Failed to fetch abuse rings')
        const data = await response.json()
        setRings(data.active_rings)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchRings()
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
        <h3 className="card-title">Active Abuse-Ring Clusters</h3>
        <p style={{ color: 'var(--text-light)', lineHeight: '1.6', fontSize: '0.95rem' }}>
          The Sentinel daemon constantly scans transaction logs for velocity clusters. It identifies organized fraud by finding instances where multiple distinct credit cards are repeatedly used from the exact same Device Fingerprint or IP Address.
        </p>
      </div>

      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {rings.map((ring, idx) => (
          <div key={idx} className="card" style={{ borderTop: '4px solid #f87171' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h4 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Cluster {ring.ring_id}</h4>
              <span style={{ backgroundColor: 'rgba(248, 113, 113, 0.1)', color: '#f87171', padding: '0.3rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                {ring.status}
              </span>
            </div>
            
            <div style={{ backgroundColor: '#0f1115', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Shared Threat Vector</div>
              <div style={{ color: '#c084fc', fontWeight: '600', marginTop: '0.3rem' }}>{ring.shared_vector}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Unique Cards Used</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>{ring.unique_cards_used}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Attempted Vol</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f87171' }}>₹{ring.total_attempted_inr.toLocaleString()}</div>
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Detected Nodes:</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {ring.nodes.map((node, nIdx) => (
                <div key={nIdx} style={{ fontSize: '0.85rem', color: 'var(--text-light)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#f87171' }}></div>
                  {node}
                </div>
              ))}
            </div>

          </div>
        ))}
      </div>

    </div>
  )
}
