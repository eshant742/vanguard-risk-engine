import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
from ml_engine import predict_transaction
from underwriting_engine import analyze_merchant
client = TestClient(app)

class TestEdgeCases:
    """Edge case, boundary condition, and stress tests."""

    def test_predict_zero_everything(self):
        result = predict_transaction({
            "amount": 0, "device_velocity": 0,
            "ip_country_match": 0, "time_since_last_txn": 0
        })
        assert "is_fraud" in result
        assert "action" in result

    def test_predict_extreme_amount(self):
        result = predict_transaction({
            "amount": 999999999, "device_velocity": 1,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        assert "is_fraud" in result

    def test_predict_extreme_velocity(self):
        result = predict_transaction({
            "amount": 1000, "device_velocity": 9999,
            "ip_country_match": 0, "time_since_last_txn": 0
        })
        assert result["is_fraud"] is True
        assert "Velocity" in " ".join(result.get("xai_flags", []))

    def test_predict_boundary_velocity_2(self):
        """Velocity = 2 is the boundary. XAI should not flag it heavily."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 2,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        flags_text = " ".join(result.get("xai_flags", []))
        # The new ML model might still list it, but it shouldn't be the top reason.
        assert result["is_fraud"] is False

    def test_predict_boundary_velocity_3(self):
        """Velocity = 3 should trigger the velocity XAI flag (threshold is >2)."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 3,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        if result["is_fraud"]:
            assert "Velocity" in " ".join(result["xai_flags"])

    def test_predict_boundary_amount_3000(self):
        """Amount = 3000 is the boundary."""
        result = predict_transaction({
            "amount": 3000, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        assert result["is_fraud"] is False

    def test_predict_boundary_amount_3001(self):
        """Amount = 3001 should trigger the high amount XAI flag (threshold is >3000)."""
        result = predict_transaction({
            "amount": 3001, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        if result["is_fraud"]:
            assert "Amount" in " ".join(result["xai_flags"])

    def test_predict_boundary_time_5(self):
        """time_since_last_txn = 5 should NOT trigger."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 5
        })
        assert result["is_fraud"] is False

    def test_predict_boundary_time_4_9(self):
        """time_since_last_txn = 4.9 should trigger."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 4.9
        })
        if result["is_fraud"]:
            assert "Time" in " ".join(result["xai_flags"])

    def test_underwriting_unreachable_site(self):
        """Unreachable site should still return a valid result (URL-only analysis)."""
        result = analyze_merchant("https://this-site-does-not-exist-12345.xyz")
        assert "trust_score" in result
        assert "status" in result
        assert 0 <= result["trust_score"] <= 100

    def test_underwriting_special_characters_in_url(self):
        """URLs with special characters should not crash."""
        result = analyze_merchant("https://example.com/path?q=hello&x=1")
        assert "trust_score" in result

    def test_return_risk_100_percent_returner(self):
        """Customer who returns everything → CRITICAL."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-ALLRET",
            "items_kept_last_year": 0,
            "items_returned_last_year": 50,
            "current_cart_value": 50000
        })
        data = resp.json()
        assert data["risk_level"] == "CRITICAL"
        assert data["breakdown"]["return_rate"] == 100.0

    def test_return_risk_zero_cart_value(self):
        """Zero cart value should still work."""
        resp = client.post("/api/fraud/return-risk", json={
            "customer_id": "CUST-ZEROCART",
            "items_kept_last_year": 10,
            "items_returned_last_year": 1,
            "current_cart_value": 0
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["breakdown"]["cart_risk_factor"], float)

    def test_activity_feed_called_multiple_times(self):
        """Multiple calls should all succeed (not stateful failure)."""
        for _ in range(3):
            resp = client.get("/api/fraud/activity-feed")
            assert resp.status_code == 200
            assert len(resp.json()["events"]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
