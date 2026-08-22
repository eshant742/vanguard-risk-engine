import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
from ml_engine import initialize_model
client = TestClient(app)

# Ensure ML model is loaded for health check
initialize_model()

class TestAPIEndpoints:
    """Integration tests for all FastAPI endpoints via TestClient."""

    def test_root_endpoint(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "Vanguard Risk Engine"
        assert "endpoints" in data
        assert len(data["modules"]) == 6

    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["ml_model_loaded"] is True
        assert "timestamp" in data

    def test_fraud_metrics_endpoint(self):
        resp = client.get("/api/fraud/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "precision" in data
        assert "recall" in data

    def test_fraud_predict_endpoint(self):
        resp = client.post("/api/fraud/predict", json={
            "amount": 5000, "device_velocity": 1,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        assert resp.status_code == 200
        assert "is_fraud" in resp.json()

    def test_fx_risk_endpoint(self):
        resp = client.get("/api/fx-risk")
        assert resp.status_code == 200
        assert "macro_risk_score" in resp.json()

    def test_underwrite_endpoint(self):
        resp = client.post("/api/underwrite", json={"url": "https://example.com"})
        assert resp.status_code == 200
        assert "trust_score" in resp.json()

