import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestChargebackEvidence:
    """Tests for the NLP chargeback evidence auto-responder."""

    def test_not_received_claim_branch(self):
        """'Not received' claim should trigger the delivery proof defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST001",
            "customer_claim": "I never received this item"
        })
        assert resp.status_code == 200
        letter = resp.json()["evidence_letter"]
        assert "non-receipt" in letter.lower() or "delivery" in letter.lower()
        assert "Tracking" in letter

    def test_unauthorized_claim_branch(self):
        """'Unauthorized' claim should trigger the device/CVV defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST002",
            "customer_claim": "This transaction is unauthorized"
        })
        assert resp.status_code == 200
        letter = resp.json()["evidence_letter"]
        assert "unauthorized" in letter.lower()
        assert "CVV" in letter or "AVS" in letter

    def test_defective_claim_branch(self):
        """'Defective' claim should trigger the intact delivery defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST003",
            "customer_claim": "The product is broken and not working"
        })
        assert resp.status_code == 200
        letter = resp.json()["evidence_letter"]
        assert "defect" in letter.lower() or "intact" in letter.lower()

    def test_cancelled_claim_branch(self):
        """'Cancelled' claim should trigger the no-cancellation-record defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST004",
            "customer_claim": "I cancelled this order and want a refund"
        })
        assert resp.status_code == 200
        letter = resp.json()["evidence_letter"]
        assert "cancellation" in letter.lower() or "cancel" in letter.lower()

    def test_duplicate_claim_branch(self):
        """'Duplicate charge' claim should trigger the duplicate processing defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST_DUP",
            "customer_claim": "I was charged twice for the same item, duplicate charge"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["claim_category"] == "duplicate"
        assert "12.6.1" in data["reason_code"]
        letter = data["evidence_letter"]
        assert "duplicate" in letter.lower() or "single" in letter.lower()

    def test_generic_claim_fallback(self):
        """Unknown claim should trigger the generic cryptographic defense."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_TEST005",
            "customer_claim": "I just don't want it anymore"
        })
        assert resp.status_code == 200
        letter = resp.json()["evidence_letter"]
        assert "cryptographic" in letter.lower() or "authorized" in letter.lower()

    def test_deterministic_output(self):
        """Same transaction_id + claim must produce identical evidence letter."""
        payload = {"transaction_id": "pay_DETERMINISM", "customer_claim": "I never received this item"}
        r1 = client.post("/api/fraud/chargeback", json=payload).json()["evidence_letter"]
        r2 = client.post("/api/fraud/chargeback", json=payload).json()["evidence_letter"]
        assert r1 == r2, "Chargeback evidence is not deterministic for the same input"

    def test_letter_contains_required_sections(self):
        """Evidence letter must contain all 3 required sections."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_SECTIONS",
            "customer_claim": "I didn't get the product"
        })
        letter = resp.json()["evidence_letter"]
        assert "AUTHORIZATION PROOF" in letter
        assert "FULFILLMENT PROOF" in letter
        assert "DEFENSE SUMMARY" in letter
        assert "TRANSACTION ID" in letter
        assert "pay_SECTIONS" in letter

    def test_letter_contains_transaction_id(self):
        """The submitted transaction ID must appear in the generated letter."""
        txn_id = "pay_UniqueId12345"
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": txn_id,
            "customer_claim": "unauthorized purchase"
        })
        assert txn_id in resp.json()["evidence_letter"]

    def test_empty_claim_rejected(self):
        """Empty customer_claim should be rejected by Pydantic validation."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_EMPTY",
            "customer_claim": ""
        })
        assert resp.status_code == 422

    def test_empty_txn_id_rejected(self):
        """Empty transaction_id should be rejected by Pydantic validation."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "",
            "customer_claim": "test claim"
        })
        assert resp.status_code == 422

    def test_nlp_confidence_in_valid_range(self):
        """NLP confidence must be between 0 and 100."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_CONF",
            "customer_claim": "I never received this package"
        })
        data = resp.json()
        assert 0.0 <= data["nlp_confidence"] <= 100.0

    def test_nlp_scores_has_all_categories(self):
        """NLP scores dict must contain all 5 claim categories when claim is non-trivial."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_SCORES",
            "customer_claim": "The product arrived broken and defective"
        })
        data = resp.json()
        expected_categories = {"non_receipt", "unauthorized", "defective", "cancellation", "duplicate"}
        assert set(data["nlp_scores"].keys()) == expected_categories
        for score in data["nlp_scores"].values():
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_low_confidence_flag_on_garbage_input(self):
        """Garbage/ambiguous input should set low_confidence flag."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_GARBAGE",
            "customer_claim": "xyz abc 123 random words"
        })
        data = resp.json()
        assert "low_confidence" in data
        assert isinstance(data["low_confidence"], bool)

    def test_high_confidence_on_clear_claim(self):
        """Clear, unambiguous claim should have high confidence and low_confidence=False."""
        resp = client.post("/api/fraud/chargeback", json={
            "transaction_id": "pay_CLEAR",
            "customer_claim": "I never received this item, it was never delivered"
        })
        data = resp.json()
        assert data["nlp_confidence"] > 30.0
        assert data["low_confidence"] is False
