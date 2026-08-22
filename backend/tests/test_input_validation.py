import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestInputValidation:
    """Tests for Pydantic input validation and error handling."""

    def test_predict_rejects_negative_amount(self):
        resp = client.post("/api/fraud/predict", json={
            "amount": -100, "device_velocity": 1,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        assert resp.status_code == 422

    def test_predict_rejects_invalid_ip_match(self):
        resp = client.post("/api/fraud/predict", json={
            "amount": 1000, "device_velocity": 1,
            "ip_country_match": 2, "time_since_last_txn": 60
        })
        assert resp.status_code == 422

    def test_predict_rejects_negative_velocity(self):
        resp = client.post("/api/fraud/predict", json={
            "amount": 1000, "device_velocity": -1,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        assert resp.status_code == 422

    def test_predict_rejects_missing_body(self):
        resp = client.post("/api/fraud/predict")
        assert resp.status_code == 422

    def test_return_risk_rejects_empty_customer_id(self):
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "",
            "items_kept_last_year": 5,
            "items_returned_last_year": 2,
            "current_cart_value": 1000
        })
        assert resp.status_code == 422

    def test_underwrite_rejects_short_url(self):
        """URL must be at least 4 characters."""
        resp = client.post("/api/underwrite", json={"url": "ab"})
        assert resp.status_code == 422

    def test_chargeback_rejects_missing_fields(self):
        resp = client.post("/api/fraud/chargeback", json={})
        assert resp.status_code == 422

