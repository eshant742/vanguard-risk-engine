import { useState } from 'react';

export default function UnderwritingDashboard() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const analyzeUrl = async (e) => {
    e.preventDefault();
    if (!url) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/underwrite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      setResult({
        status: "ERROR",
        trust_score: 0,
        action_color: "red",
        summary: "Failed to connect to backend AI engine."
      });
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Merchant Underwriting Engine</h2>
          <p className="subtitle">AI-powered risk profiling & compliance check.</p>
        </div>
      </div>

      <div className="glass-card">
        <h3>Submit New Merchant</h3>
        <form onSubmit={analyzeUrl} className="input-group">
          <input 
            type="text" 
            className="input-field" 
            placeholder="Enter merchant website URL (e.g., https://example.com)" 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <div className="loader"></div> : 'Run AI Analysis'}
          </button>
        </form>

        {result && (
          <div className="glass-card" style={{ marginTop: '2rem', background: 'rgba(0,0,0,0.3)' }}>
            <div className="result-header">
              <div>
                <h3 style={{ color: '#fff', marginBottom: '0.2rem' }}>AI Risk Report</h3>
                <p style={{ color: 'var(--text-muted)' }}>{result.url}</p>
              </div>
              <div className="score-display">
                <div className={`score-value ${result.action_color}`}>{result.trust_score}</div>
                <div className="score-label">Trust Score</div>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <span className={`badge badge-${result.action_color}`} style={{ fontSize: '1rem', padding: '0.6rem 1rem' }}>
                <span className={`pulse-indicator bg-${result.action_color}`} style={{ marginRight: '0.5rem' }}></span>
                ACTION: {result.status}
              </span>
            </div>

            <p style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>{result.summary}</p>

            {result.flags && (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {result.flags.prohibited_items && result.flags.prohibited_items.length > 0 && (
                  <div>
                    <h4 style={{ color: '#feb2b2', marginBottom: '0.5rem' }}>Prohibited Items Found</h4>
                    <ul className="flag-list">
                      {result.flags.prohibited_items.map((item, i) => (
                        <li key={i} className="flag-item">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {result.flags.high_risk_items && result.flags.high_risk_items.length > 0 && (
                  <div>
                    <h4 style={{ color: '#fbd38d', marginBottom: '0.5rem' }}>High-Risk Terms Found</h4>
                    <ul className="flag-list">
                      {result.flags.high_risk_items.map((item, i) => (
                        <li key={i} className="flag-item" style={{ background: 'rgba(214, 158, 46, 0.15)', color: '#fbd38d', borderColor: 'rgba(214, 158, 46, 0.3)' }}>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
