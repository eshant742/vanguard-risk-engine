import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestAbuseRingSentinel:
    """Tests for the abuse-ring detection sentinel."""

    def test_abuse_ring_endpoint_returns_200(self):
        resp = client.get("/api/fraud/abuse-ring")
        assert resp.status_code == 200

    def test_abuse_ring_has_required_fields(self):
        data = client.get("/api/fraud/abuse-ring").json()
        assert "scan_timestamp" in data
        assert "total_transactions_scanned" in data
        assert "active_rings" in data
        assert isinstance(data["active_rings"], list)

    def test_abuse_ring_timestamp_is_iso_format(self):
        """Scan timestamp should be valid ISO 8601."""
        data = client.get("/api/fraud/abuse-ring").json()
        # Should not raise ValueError
        from datetime import datetime
        datetime.fromisoformat(data["scan_timestamp"].replace("Z", "+00:00"))

    def test_each_ring_has_required_structure(self):
        """Every detected ring must have all required fields."""
        data = client.get("/api/fraud/abuse-ring").json()
        for ring in data["active_rings"]:
            assert "ring_id" in ring
            assert "shared_vector" in ring
            assert "unique_cards_used" in ring
            assert "total_attempted_inr" in ring
            assert "status" in ring
            assert "detection_method" in ring
            assert "nodes" in ring
            assert isinstance(ring["nodes"], list)
            assert len(ring["nodes"]) > 0
            # Card count should match node count
            assert ring["unique_cards_used"] == len(ring["nodes"])

    def test_all_rings_are_blocked(self):
        """All detected rings should have BLOCKED status."""
        data = client.get("/api/fraud/abuse-ring").json()
        for ring in data["active_rings"]:
            assert "BLOCKED" in ring["status"]

    def test_three_detection_methods_covered(self):
        """Should demonstrate 3 different detection methods."""
        data = client.get("/api/fraud/abuse-ring").json()
        methods = {ring["detection_method"] for ring in data["active_rings"]}
        assert len(methods) >= 3, f"Only {len(methods)} distinct detection methods"

