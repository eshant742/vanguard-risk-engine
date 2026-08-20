import { useState, useEffect } from 'react';

export default function FXRiskDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('');

  const fetchData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/fx-risk');
      const result = await response.json();
      setData(result);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Failed to fetch FX data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto refresh every 30 seconds to simulate real-time dashboard
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}><div className="loader" style={{ width: '40px', height: '40px' }}></div></div>;
  }

  if (!data) return <div>Failed to load FX Risk Engine</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h2>Macroeconomic FX & Liquidity Risk</h2>
          <p className="subtitle">Real-time global currency monitoring and sentiment-based risk prediction.</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>System Risk Level</div>
          <span className={`badge badge-${data.status_color}`} style={{ fontSize: '1.1rem', padding: '0.6rem 1.2rem' }}>
            <span className={`pulse-indicator bg-${data.status_color}`} style={{ marginRight: '0.5rem' }}></span>
            {data.system_status}
          </span>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>Last updated: {lastUpdated}</div>
        </div>
      </div>

      <div className="fx-ticker">
        {Object.entries(data.rates).map(([currency, rate]) => (
          <div key={currency} className="fx-item">
            <span className="fx-pair">{data.base_currency} / {currency}</span>
            <span className="fx-rate">{rate.toFixed(2)}</span>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="glass-card">
          <div className="result-header" style={{ marginBottom: '1rem', paddingBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#fff' }}>Settlement Risk Score</h3>
            <div className={`score-value ${data.status_color}`}>{data.macro_risk_score}</div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Score is calculated by blending real-time FX volatility with live NLP sentiment analysis of global financial news. 
            Scores &gt; 75 trigger automated spread widening.
          </p>
          
          <div style={{ marginTop: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <span>0 (Stable)</span>
              <span>100 (Critical)</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div 
                style={{ 
                  width: `${data.macro_risk_score}%`, 
                  height: '100%', 
                  background: `var(--accent-${data.status_color})`,
                  transition: 'width 1s ease-in-out'
                }}
              ></div>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ color: '#fff', marginBottom: '1.5rem' }}>Live AI News Sentiment (RSS)</h3>
          <div className="news-feed">
            {data.news.map((item, index) => (
              <div key={index} className={`news-item border-${item.color}`}>
                <div>
                  <div className="news-title">{item.headline}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    VADER Sentiment Score: <span className={`text-${item.color}`}>{item.sentiment.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
