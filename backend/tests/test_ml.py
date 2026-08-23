import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
from ml_engine import initialize_model, predict_transaction, generate_synthetic_data, FEATURE_COLUMNS

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
            assert len(result["xai_flags"]) >= 2

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

