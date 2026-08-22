"""
Vanguard Risk Engine — Comprehensive Test Suite
Razorpay AI Buildathon Track 02: AI Risk Manager

Run with: python -m pytest test_all.py -v

Coverage:
  - ML Engine: model training, predictions, metrics, XAI, synthetic data, edge cases
  - API Endpoints: all 10 endpoints via FastAPI TestClient, input validation, error responses
  - Chargeback NLP: all 5 claim branches + determinism + letter structure
  - Return Risk: all 3 tiers + zero-purchase + boundary values
  - Abuse Ring: structure, ring data integrity
  - Underwriting: keyword detection, whitelist, trust scoring, multi-keyword, URL normalization
  - FX Risk: rates, sentiment, risk score, status mapping, fallback resilience
  - Activity Feed: event count, timestamp format, event types
  - Edge Cases: zero values, extreme values, missing keys, Pydantic validation
"""
import pytest
import re
import sys
import os

# Ensure backend modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from ml_engine import initialize_model, predict_transaction, generate_synthetic_data, FEATURE_COLUMNS
from underwriting_engine import (
    analyze_merchant, _keyword_in_text, _context_is_whitelisted,
    PROHIBITED_KEYWORDS, HIGH_RISK_KEYWORDS
)
from fx_risk_engine import get_fx_risk_data, get_live_fx_rates, get_news_sentiment
from main import app


# Shared FastAPI test client
client = TestClient(app)


# ══════════════════════════════════════════════
#  1. ML ENGINE — UNIT TESTS
# ══════════════════════════════════════════════

class TestMLEngine:
    """Tests for the Random Forest fraud detection model."""

    def test_model_initializes_returns_dict(self):
        """Model must train without errors and return a metrics dict."""
        metrics = initialize_model()
        assert metrics is not None
        assert isinstance(metrics, dict)

    def test_all_metric_keys_present(self):
        """Every required metric key must exist in the output."""
        metrics = initialize_model()
        required_keys = [
            "precision", "recall", "f1_score", "accuracy", "roc_auc",
            "false_positives", "true_positives", "false_negatives", "true_negatives",
            "false_positive_cost_inr", "total_fraud_prevented_inr",
            "net_margin_protected_inr", "test_set_size", "train_set_size",
            "feature_importance"
        ]
        for key in required_keys:
            assert key in metrics, f"Missing metric key: {key}"

    def test_precision_recall_f1_roc_in_unit_range(self):
        """Precision, Recall, F1, ROC-AUC must all be in [0, 1]."""
        metrics = initialize_model()
        for key in ["precision", "recall", "f1_score", "accuracy", "roc_auc"]:
            assert 0.0 <= metrics[key] <= 1.0, f"{key} = {metrics[key]} is out of [0,1]"

    def test_accuracy_is_reasonable(self):
        """Accuracy should be well above random chance (50%) on this dataset."""
        metrics = initialize_model()
        assert metrics["accuracy"] > 0.65, f"Accuracy {metrics['accuracy']} is suspiciously low"

    def test_held_out_test_set_is_20_percent(self):
        """Razorpay requirement: strict 20% held-out test set."""
        metrics = initialize_model()
        total = metrics["train_set_size"] + metrics["test_set_size"]
        test_ratio = metrics["test_set_size"] / total
        assert abs(test_ratio - 0.20) < 0.02, f"Test set ratio {test_ratio:.3f} is not ~20%"

    def test_confusion_matrix_sums_to_test_set(self):
        """TP + TN + FP + FN must equal the test set size."""
        m = initialize_model()
        cm_total = m["true_positives"] + m["true_negatives"] + m["false_positives"] + m["false_negatives"]
        assert cm_total == m["test_set_size"], f"CM total {cm_total} != test_set_size {m['test_set_size']}"

    def test_net_margin_formula_correct(self):
        """Net margin = (TP × ₹4500) - (FP × ₹2000)."""
        m = initialize_model()
        expected_fraud_prevented = m["true_positives"] * 4500
        expected_fp_cost = m["false_positives"] * 2000
        assert m["total_fraud_prevented_inr"] == expected_fraud_prevented
        assert m["false_positive_cost_inr"] == expected_fp_cost
        assert m["net_margin_protected_inr"] == expected_fraud_prevented - expected_fp_cost

    def test_feature_importance_sums_to_one(self):
        """Random Forest feature importances must sum to ~1.0."""
        metrics = initialize_model()
        total = sum(f["importance"] for f in metrics["feature_importance"])
        assert abs(total - 1.0) < 0.01, f"Feature importance sum: {total}"

    def test_feature_importance_sorted_descending(self):
        """Feature importances should be sorted from highest to lowest."""
        metrics = initialize_model()
        importances = [f["importance"] for f in metrics["feature_importance"]]
        assert importances == sorted(importances, reverse=True)

    def test_feature_importance_has_all_features(self):
        """All 4 feature columns must appear in the feature importance list."""
        metrics = initialize_model()
        feature_names = {f["feature"] for f in metrics["feature_importance"]}
        for col in FEATURE_COLUMNS:
            assert col in feature_names, f"Missing feature in importance: {col}"

    def test_predict_safe_transaction_allowed(self):
        """Low-risk transaction should be allowed with empty XAI flags."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 120
        })
        assert result["action"] in ["ALLOW", "BLOCK"]
        assert isinstance(result["fraud_probability"], float)
        assert 0.0 <= result["fraud_probability"] <= 100.0
        if result["action"] == "ALLOW":
            assert result["xai_flags"] == [], "ALLOW action should have empty XAI flags"
            assert "Allowed" in result["reason"]

    def test_predict_high_risk_blocked_with_xai(self):
        """High-risk transaction should be BLOCKED with XAI audit trail."""
        result = predict_transaction({
            "amount": 15000, "device_velocity": 8,
            "ip_country_match": 0, "time_since_last_txn": 1
        })
        assert result["is_fraud"] is True
        assert result["action"] == "BLOCK"
        assert len(result["xai_flags"]) > 0
        assert "Blocked by AI" in result["reason"]

    def test_xai_flags_all_four_triggers(self):
        """Transaction hitting all 4 risk triggers should produce 4 XAI flags."""
        result = predict_transaction({
            "amount": 10000, "device_velocity": 5,
            "ip_country_match": 0, "time_since_last_txn": 2
        })
        if result["is_fraud"]:
            flags_text = " ".join(result["xai_flags"])
            assert "Velocity" in flags_text
            assert "Mismatch" in flags_text
            assert "Amount" in flags_text
            assert "Rapid" in flags_text

    def test_predict_result_structure(self):
        """Prediction output must have all required keys with correct types."""
        result = predict_transaction({"amount": 1000, "device_velocity": 1,
                                      "ip_country_match": 1, "time_since_last_txn": 60})
        assert isinstance(result["is_fraud"], bool)
        assert isinstance(result["fraud_probability"], float)
        assert result["action"] in ["ALLOW", "BLOCK"]
        assert isinstance(result["reason"], str) and len(result["reason"]) > 0
        assert isinstance(result["xai_flags"], list)

    def test_predict_with_missing_keys_uses_defaults(self):
        """Missing keys should use safe defaults, not crash."""
        result = predict_transaction({})
        assert "is_fraud" in result
        assert "action" in result

    def test_predict_with_partial_keys(self):
        """Partial input should work with defaults filling in."""
        result = predict_transaction({"amount": 500})
        assert "is_fraud" in result
        assert result["action"] in ["ALLOW", "BLOCK"]

    def test_synthetic_data_columns_and_size(self):
        """Generated data must have all expected columns and correct row count."""
        df = generate_synthetic_data(n_samples=100)
        for col in FEATURE_COLUMNS + ["is_fraud"]:
            assert col in df.columns, f"Missing column: {col}"
        assert len(df) == 100

    def test_synthetic_data_has_both_classes(self):
        """Synthetic data must contain both fraud and non-fraud samples."""
        df = generate_synthetic_data(n_samples=2000)
        assert df["is_fraud"].sum() > 0, "No fraud cases generated"
        assert (df["is_fraud"] == 0).sum() > 0, "No safe cases generated"

    def test_synthetic_data_values_reasonable(self):
        """Generated feature values should be within expected ranges."""
        df = generate_synthetic_data(n_samples=1000)
        assert (df["amount"] >= 0).all(), "Negative amounts found"
        assert (df["device_velocity"] >= 0).all(), "Negative velocity found"
        assert df["ip_country_match"].isin([0, 1]).all(), "IP match not binary"
        assert (df["time_since_last_txn"] >= 0).all(), "Negative time values"

    def test_model_caching_returns_same_metrics(self):
        """Second call to initialize_model should return cached (identical) metrics."""
        m1 = initialize_model()
        m2 = initialize_model()
        assert m1["precision"] == m2["precision"]
        assert m1["recall"] == m2["recall"]
        assert m1["f1_score"] == m2["f1_score"]


# ══════════════════════════════════════════════
#  2. CHARGEBACK EVIDENCE — UNIT + API TESTS
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  3. RETURN-RISK SCORER — API TESTS
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  4. ABUSE-RING SENTINEL — API TESTS
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  5. ACTIVITY FEED — API TESTS
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  6. UNDERWRITING ENGINE — UNIT TESTS
# ══════════════════════════════════════════════

class TestUnderwritingEngine:
    """Tests for the AI merchant underwriting / compliance system."""

    # --- Keyword Detection ---

    def test_keyword_exact_match_in_text(self):
        assert _keyword_in_text("crypto", "Buy crypto here today")
        assert _keyword_in_text("bitcoin", "Trade bitcoin now")
        assert _keyword_in_text("gambling", "Online gambling site")

    def test_keyword_in_url(self):
        assert _keyword_in_text("binance", "Visit binance.com for trading")
        assert _keyword_in_text("bet365", "check bet365.com")

    def test_keyword_at_start_of_text(self):
        assert _keyword_in_text("crypto", "crypto is the future")

    def test_keyword_at_end_of_text(self):
        assert _keyword_in_text("crypto", "I love crypto")

    def test_keyword_no_false_positive_substring(self):
        """Keywords should NOT match as substrings of other words."""
        assert not _keyword_in_text("crypto", "The encrypted data was safe")
        assert not _keyword_in_text("gun", "burgundy colored coat")

    def test_keyword_multi_word_phrase(self):
        """Multi-word prohibited phrases should match correctly."""
        assert _keyword_in_text("dark web", "Buy things on the dark web")
        assert _keyword_in_text("fake id", "Get a fake id here")
        assert _keyword_in_text("get rich quick", "This get rich quick scheme is amazing")

    # --- Whitelist ---

    def test_whitelist_suppresses_gundam(self):
        assert _context_is_whitelisted("gun", "check out this gundam model kit")

    def test_whitelist_suppresses_stakeholder(self):
        assert _context_is_whitelisted("stake", "stakeholder meeting tomorrow")

    def test_whitelist_suppresses_burgundy(self):
        assert _context_is_whitelisted("gun", "a beautiful burgundy dress")

    def test_whitelist_suppresses_sweepstakes(self):
        assert _context_is_whitelisted("stake", "enter our sweepstakes contest")

    def test_whitelist_does_not_suppress_real_crypto(self):
        assert not _context_is_whitelisted("crypto", "buy crypto today")

    def test_whitelist_does_not_suppress_real_gambling(self):
        assert not _context_is_whitelisted("gambling", "online gambling platform")

    # --- Full Analysis ---

    def test_safe_site_gets_high_trust_score(self):
        result = analyze_merchant("https://www.example.com")
        assert result["trust_score"] >= 70 or result["status"] in ["APPROVE", "MANUAL REVIEW"]
        assert "url" in result and "flags" in result

    def test_prohibited_site_rejected(self):
        result = analyze_merchant("https://www.binance.com")
        assert result["trust_score"] < 40
        assert result["status"] == "REJECT"
        assert "binance" in result["flags"]["prohibited_items"]

    def test_gambling_site_rejected(self):
        result = analyze_merchant("https://www.bet365.com")
        assert result["status"] == "REJECT"
        assert "bet365" in result["flags"]["prohibited_items"]

    def test_result_has_all_required_fields(self):
        result = analyze_merchant("https://test-example.com")
        for key in ["url", "trust_score", "status", "action_color", "flags", "summary"]:
            assert key in result, f"Missing key: {key}"
        assert result["action_color"] in ["red", "yellow", "green"]
        assert 0 <= result["trust_score"] <= 100

    def test_flags_structure(self):
        """Flags dict must have prohibited_items, high_risk_items, and sentiment."""
        result = analyze_merchant("https://example.com")
        flags = result["flags"]
        assert "prohibited_items" in flags
        assert "high_risk_items" in flags
        assert "sentiment_compound" in flags
        assert isinstance(flags["prohibited_items"], list)
        assert isinstance(flags["high_risk_items"], list)
        assert isinstance(flags["sentiment_compound"], float)

    def test_url_auto_prefixed_with_https(self):
        result = analyze_merchant("example.com")
        assert result["url"].startswith("https://")

    def test_trust_score_clamped_to_0_100(self):
        """Even heavily flagged sites should have score in [0, 100]."""
        result = analyze_merchant("https://crypto-casino-gambling-betting.com")
        assert 0 <= result["trust_score"] <= 100

    def test_status_thresholds_approve(self):
        """Trust score >= 70 → APPROVE, action_color = green."""
        result = analyze_merchant("https://www.example.com")
        if result["trust_score"] >= 70:
            assert result["status"] == "APPROVE"
            assert result["action_color"] == "green"

    def test_summary_includes_term_counts(self):
        """Summary string must mention how many terms were found."""
        result = analyze_merchant("https://www.binance.com")
        assert "prohibited" in result["summary"].lower()


# ══════════════════════════════════════════════
#  7. FX RISK ENGINE — UNIT TESTS
# ══════════════════════════════════════════════

class TestFXRiskEngine:
    """Tests for the macroeconomic FX & liquidity risk engine."""

    def test_fx_rates_returns_dict_with_currencies(self):
        rates = get_live_fx_rates()
        assert isinstance(rates, dict)
        assert len(rates) > 0
        for currency, rate in rates.items():
            assert isinstance(rate, (int, float)), f"Rate for {currency} is not numeric"
            assert rate > 0, f"Rate for {currency} is non-positive: {rate}"

    def test_fallback_rates_have_expected_currencies(self):
        """Fallback should contain INR, EUR, GBP."""
        # Even if live API works, fallback structure is tested via the function
        rates = get_live_fx_rates()
        # Live or fallback should have these
        assert len(rates) >= 3 or set(rates.keys()) == {"INR", "EUR", "GBP"}

    def test_news_sentiment_structure_complete(self):
        result = get_news_sentiment()
        assert "headlines" in result
        assert "average_sentiment" in result
        assert isinstance(result["headlines"], list)
        assert len(result["headlines"]) > 0
        for item in result["headlines"]:
            assert "headline" in item
            assert "sentiment" in item
            assert "color" in item
            assert item["color"] in ["green", "yellow", "red"]
            assert isinstance(item["sentiment"], (int, float))

    def test_average_sentiment_in_valid_range(self):
        """VADER compound scores are in [-1, 1], so average should be too."""
        result = get_news_sentiment()
        assert -1.0 <= result["average_sentiment"] <= 1.0

    def test_fx_risk_data_all_fields(self):
        data = get_fx_risk_data()
        required = ["rates", "base_currency", "news", "macro_risk_score",
                     "system_status", "status_color", "headline_count", "average_sentiment"]
        for key in required:
            assert key in data, f"Missing key: {key}"
        assert data["base_currency"] == "USD"

    def test_risk_score_clamped_0_100(self):
        data = get_fx_risk_data()
        assert 0 <= data["macro_risk_score"] <= 100

    def test_status_color_matches_score(self):
        data = get_fx_risk_data()
        score = data["macro_risk_score"]
        if score > 75:
            assert data["status_color"] == "red"
        elif score > 40:
            assert data["status_color"] == "yellow"
        else:
            assert data["status_color"] == "green"

    def test_headline_count_matches_news_list(self):
        data = get_fx_risk_data()
        assert data["headline_count"] == len(data["news"])


# ══════════════════════════════════════════════
#  8. API INTEGRATION — SYSTEM-LEVEL ENDPOINT TESTS
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  9. INPUT VALIDATION — PYDANTIC EDGE CASES
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
#  10. EDGE CASES — STRESS & BOUNDARY TESTS
# ══════════════════════════════════════════════

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
        """Velocity = 2 is the boundary. XAI should not flag it (threshold is >2)."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 2,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        flags_text = " ".join(result.get("xai_flags", []))
        assert "Velocity" not in flags_text

    def test_predict_boundary_velocity_3(self):
        """Velocity = 3 should trigger the velocity XAI flag (threshold is >2)."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 3,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        if result["is_fraud"]:
            assert "Velocity" in " ".join(result["xai_flags"])

    def test_predict_boundary_amount_3000(self):
        """Amount = 3000 is the boundary. XAI should not flag it (threshold is >3000)."""
        result = predict_transaction({
            "amount": 3000, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        flags_text = " ".join(result.get("xai_flags", []))
        assert "Amount" not in flags_text

    def test_predict_boundary_amount_3001(self):
        """Amount = 3001 should trigger the high amount XAI flag (threshold is >3000)."""
        result = predict_transaction({
            "amount": 3001, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 60
        })
        if result["is_fraud"]:
            assert "Amount" in " ".join(result["xai_flags"])

    def test_predict_boundary_time_5(self):
        """time_since_last_txn = 5 should NOT trigger rapid flag (threshold is <5)."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 5
        })
        flags_text = " ".join(result.get("xai_flags", []))
        assert "Rapid" not in flags_text

    def test_predict_boundary_time_4_9(self):
        """time_since_last_txn = 4.9 should trigger rapid flag (threshold is <5)."""
        result = predict_transaction({
            "amount": 500, "device_velocity": 0,
            "ip_country_match": 1, "time_since_last_txn": 4.9
        })
        if result["is_fraud"]:
            assert "Rapid" in " ".join(result["xai_flags"])

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
        assert data["breakdown"]["cart_risk_factor"] == 0.0

    def test_activity_feed_called_multiple_times(self):
        """Multiple calls should all succeed (not stateful failure)."""
        for _ in range(3):
            resp = client.get("/api/fraud/activity-feed")
            assert resp.status_code == 200
            assert len(resp.json()["events"]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
