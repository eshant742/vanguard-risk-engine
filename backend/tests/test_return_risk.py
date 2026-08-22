import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestReturnRiskScorer:
    """Tests for the wardrobing fraud return-risk scorer."""

    def test_zero_purchases_returns_low_risk(self):
        """New customer with no history should get LOW risk and base probability."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-NEW",
            "items_kept_last_year": 0,
            "items_returned_last_year": 0,
            "current_cart_value": 1000
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "LOW"
        assert data["return_probability"] == 10.0
        assert data["action"] == "STANDARD_POLICY"

    def test_high_return_rate_critical(self):
        """Customer with 80% return rate should get CRITICAL risk."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-SERIAL",
            "items_kept_last_year": 2,
            "items_returned_last_year": 8,
            "current_cart_value": 15000
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "CRITICAL"
        assert data["action"] == "DISABLE_FREE_RETURNS"
        assert data["return_probability"] > 75.0

    def test_moderate_return_rate_medium(self):
        """Customer with ~50% return rate should get MEDIUM risk."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-MED",
            "items_kept_last_year": 5,
            "items_returned_last_year": 5,
            "current_cart_value": 5000
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "MEDIUM"
        assert data["action"] == "WARNING_PROMPT"

    def test_low_return_rate_low_risk(self):
        """Loyal customer with very few returns should get LOW risk."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-LOYAL",
            "items_kept_last_year": 20,
            "items_returned_last_year": 1,
            "current_cart_value": 2000
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "LOW"
        assert data["action"] == "STANDARD_POLICY"

    def test_return_probability_capped_at_99_9(self):
        """Return probability should never exceed 99.9%."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-EXTREME",
            "items_kept_last_year": 0,
            "items_returned_last_year": 100,
            "current_cart_value": 999999
        })
        data = resp.json()
        assert data["return_probability"] <= 99.9

    def test_response_includes_breakdown(self):
        """Response must include the risk breakdown with all factors."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-BD",
            "items_kept_last_year": 5,
            "items_returned_last_year": 5,
            "current_cart_value": 10000
        })
        data = resp.json()
        assert "breakdown" in data
        bd = data["breakdown"]
        assert "return_rate" in bd
        assert "cart_risk_factor" in bd
        assert "history_factor" in bd

    def test_cart_risk_factor_capped_at_10(self):
        """Cart risk factor should not exceed 10 even for very high cart values."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-BIGCART",
            "items_kept_last_year": 10,
            "items_returned_last_year": 1,
            "current_cart_value": 500000
        })
        data = resp.json()
        assert data["breakdown"]["cart_risk_factor"] <= 10.0

    def test_pydantic_rejects_negative_items(self):
        """Negative item counts should be rejected."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-NEG",
            "items_kept_last_year": -1,
            "items_returned_last_year": 5,
            "current_cart_value": 1000
        })
        assert resp.status_code == 422

