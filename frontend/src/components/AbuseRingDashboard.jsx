import { useState, useEffect } from 'react'
import { Scan } from 'lucide-react'
import { API_BASE } from '../App'

export default function AbuseRingDashboard() {
  const [rings, setRings] = useState([])
  const [scanInfo, setScanInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasScanned, setHasScanned] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)

  const fetchRings = async (showScanAnimation = false) => {
    if (showScanAnimation) {
      setScanning(true)
      setScanProgress(0)
      setRings([])
      
      // Simulate scan progress
      const progressInterval = setInterval(() => {
        setScanProgress(prev => {
          if (prev >= 95) {
            clearInterval(progressInterval)
            return 95
          }
          return prev + Math.random() * 15
        })
      }, 200)

      // Wait for visual effect before actually fetching
      await new Promise(resolve => setTimeout(resolve, 2000))
      clearInterval(progressInterval)
      setScanProgress(100)
    } else {
      setLoading(true)
    }

    try {
      const response = await fetch(`${API_BASE}/api/fraud/abuse-ring`)
      if (!response.ok) throw new Error('Failed to fetch abuse rings')
      const data = await response.json()
      setRings(data.active_rings)
      setScanInfo({
        timestamp: data.scan_timestamp,
        totalScanned: data.total_transactions_scanned
      })
      setHasScanned(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setScanning(false)
    }
  }

  // Auto-load on mount
  useEffect(() => {
    fetchRings(false)
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
      </div>
    )
  }

  if (error && !hasScanned) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#f87171' }}>
        {error}. Make sure the Python backend is running!
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 className="card-title">Active Abuse-Ring Clusters</h3>
            <p style={{ color: 'var(--text-light)', lineHeight: '1.6', fontSize: '0.95rem' }}>
              The Sentinel daemon constantly scans transaction logs for velocity clusters. It identifies organized fraud by finding instances where multiple distinct credit cards are repeatedly used from the exact same Device Fingerprint, IP Address, or Shipping Address.
            </p>
          </div>
          <button 
            className="primary-btn" 
            onClick={() => fetchRings(true)}
            disabled={scanning}
            style={{ marginLeft: '1rem', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Scan size={16} />
            {scanning ? 'Scanning...' : 'Re-Scan Now'}
          </button>
        </div>

        {scanInfo && (
          <div style={{ marginTop: '1rem', display: 'flex', gap: '2rem', fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
            <span>Transactions Scanned: <span style={{ color: 'var(--cyber-cyan)' }}>{scanInfo.totalScanned?.toLocaleString()}</span></span>
            <span>Rings Detected: <span style={{ color: '#f87171' }}>{rings.length}</span></span>
          </div>
        )}
      </div>

      {/* Scanning animation */}
      {scanning && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
          <div style={{ fontSize: '1.1rem', color: 'var(--cyber-cyan)', fontFamily: "'JetBrains Mono', monospace", marginBottom: '1.5rem' }}>
            Scanning {Math.round(scanProgress)}% of transaction logs...
          </div>
          <div style={{ width: '100%', height: '4px', background: 'var(--panel-charcoal)', borderRadius: '2px', overflow: 'hidden', marginBottom: '1rem' }}>
            <div style={{ width: `${scanProgress}%`, height: '100%', background: 'var(--cyber-cyan)', transition: 'width 0.3s ease', boxShadow: '0 0 10px var(--cyber-cyan-glow)' }}></div>
          </div>
          <div className="scan-line" style={{ marginBottom: '0.5rem' }}></div>
          <div className="scan-line" style={{ animationDelay: '0.3s' }}></div>
          <div className="scan-line" style={{ animationDelay: '0.6s' }}></div>
        </div>
      )}

      {!scanning && (
        <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))' }}>
          {rings.map((ring, idx) => (
            <div key={idx} className="card animate-fade-in" style={{ borderTop: '4px solid #f87171', animationDelay: `${idx * 0.15}s` }}>
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

              {ring.detection_method && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem', fontFamily: "'JetBrains Mono', monospace" }}>
                  Detection: <span style={{ color: 'var(--cyber-cyan)' }}>{ring.detection_method}</span>
                </div>
              )}

              {ring.graph_metrics && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem', backgroundColor: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '4px' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SUBGRAPH DENSITY</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-light)', fontFamily: "'JetBrains Mono', monospace" }}>{ring.graph_metrics.subgraph_density}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SHARING RATIO</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-light)', fontFamily: "'JetBrains Mono', monospace" }}>{ring.graph_metrics.sharing_ratio}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AVG PAGERANK</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-light)', fontFamily: "'JetBrains Mono', monospace" }}>{ring.graph_metrics.avg_pagerank}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DEGREE CENTRALITY</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-light)', fontFamily: "'JetBrains Mono', monospace" }}>{ring.graph_metrics.avg_degree_centrality}</div>
                  </div>
                </div>
              )}

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
      )}

    </div>
  )
}
