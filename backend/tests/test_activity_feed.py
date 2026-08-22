import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestActivityFeed:
    """Tests for the live activity feed / threat ticker."""

    def test_activity_feed_returns_200(self):
        resp = client.get("/api/fraud/activity-feed")
        assert resp.status_code == 200

    def test_activity_feed_returns_8_events(self):
        data = client.get("/api/fraud/activity-feed").json()
        assert "events" in data
        assert len(data["events"]) == 8

    def test_event_structure(self):
        """Each event must have timestamp, type, and message."""
        data = client.get("/api/fraud/activity-feed").json()
        for event in data["events"]:
            assert "timestamp" in event
            assert "type" in event
            assert "message" in event
            assert isinstance(event["message"], str) and len(event["message"]) > 0

    def test_event_timestamps_valid_format(self):
        """Timestamps must be in HH:MM:SS format with valid values."""
        data = client.get("/api/fraud/activity-feed").json()
        for event in data["events"]:
            ts = event["timestamp"]
            parts = ts.split(":")
            assert len(parts) == 3, f"Invalid timestamp format: {ts}"
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            assert 0 <= h <= 23, f"Hour {h} out of range in {ts}"
            assert 0 <= m <= 59, f"Minute {m} out of range in {ts}"
            assert 0 <= s <= 59, f"Second {s} out of range in {ts}"

    def test_event_types_are_valid(self):
        """Event types must be from the known categories."""
        valid_types = {"fraud_block", "chargeback_win", "abuse_ring", "return_fraud", "underwriting"}
        data = client.get("/api/fraud/activity-feed").json()
        for event in data["events"]:
            assert event["type"] in valid_types, f"Unknown event type: {event['type']}"

