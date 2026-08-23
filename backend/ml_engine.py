import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    accuracy_score, roc_auc_score, confusion_matrix
)
import shap

# Consistent feature ordering — prevents sklearn warnings
FEATURE_COLUMNS = ['amount', 'device_velocity', 'ip_country_match', 'time_since_last_txn']

# 1. Generate Synthetic Merchant Transactions
def generate_synthetic_data(n_samples=5000):
    np.random.seed(42)
    
    # Features:
    # amount: transaction amount in INR
    # device_velocity: number of txns from this device in the last hour
    # ip_country_match: 1 if IP matches card issuing country, 0 if mismatch
    # time_since_last_txn: minutes since last transaction for this user
    
    amounts = np.random.exponential(scale=2000, size=n_samples)
    device_velocity = np.random.poisson(lam=1.5, size=n_samples)
    ip_country_match = np.random.choice([0, 1], p=[0.1, 0.9], size=n_samples)
    time_since_last_txn = np.random.exponential(scale=60, size=n_samples)
    
    # Create Labels (is_fraud) based on rules (adding some noise)
    # Fraudsters usually have: High device velocity, IP mismatch, short time between txns
    is_fraud = np.zeros(n_samples, dtype=int)
    
    for i in range(n_samples):
        risk_score = 0
        if device_velocity[i] > 2: risk_score += 2
        if ip_country_match[i] == 0: risk_score += 3
        if amounts[i] > 3000: risk_score += 1
        if time_since_last_txn[i] < 5: risk_score += 1
        
        # Add random noise so model has to actually learn
        if risk_score + np.random.normal(0, 1.5) > 2.5:
            is_fraud[i] = 1
            
    df = pd.DataFrame({
        'amount': amounts,
        'device_velocity': device_velocity,
        'ip_country_match': ip_country_match,
        'time_since_last_txn': time_since_last_txn,
        'is_fraud': is_fraud
    })
    return df

# Global model state
clf = None
explainer = None
metrics_cache = None

def initialize_model():
    global clf, explainer, metrics_cache
    if clf is not None:
        return metrics_cache
        
    df = generate_synthetic_data()
    
    X = df[FEATURE_COLUMNS]
    y = df['is_fraud']
    
    # Strictly follow Razorpay rule: "held-out test set"
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    # Train model
    clf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
    clf.fit(X_train, y_train)
    
    # Initialize SHAP explainer
    explainer = shap.TreeExplainer(clf)
    
    # Evaluate on held-out test set
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)
    
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)
    
    # ROC-AUC (handles edge case where only one class exists)
    try:
        roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
    except (ValueError, IndexError):
        roc_auc = 0.0
    
    cm = confusion_matrix(y_test, y_pred)
    
    is_full_matrix = cm.shape[0] > 1 and cm.shape[1] > 1
    false_positives = int(cm[0][1]) if is_full_matrix else 0
    true_positives = int(cm[1][1]) if is_full_matrix else 0
    false_negatives = int(cm[1][0]) if is_full_matrix else 0
    true_negatives = int(cm[0][0]) if cm.shape[0] > 0 and cm.shape[1] > 0 else 0
    
    total_false_positive_cost = false_positives * 2000
    total_fraud_prevented_value = true_positives * 4500
    net_margin_protected = total_fraud_prevented_value - total_false_positive_cost
    
    importances = clf.feature_importances_
    feature_importance = []
    for fname, imp in sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True):
        feature_importance.append({
            "feature": fname,
            "importance": round(float(imp), 4)
        })
    
    metrics_cache = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "roc_auc": round(roc_auc, 4),
        "false_positives": false_positives,
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "false_positive_cost_inr": total_false_positive_cost,
        "total_fraud_prevented_inr": total_fraud_prevented_value,
        "net_margin_protected_inr": net_margin_protected,
        "test_set_size": len(y_test),
        "train_set_size": len(y_train),
        "feature_importance": feature_importance
    }
    return metrics_cache

def predict_transaction(txn_data: dict):
    if clf is None:
        initialize_model()
    
    features = pd.DataFrame([{
        'amount': txn_data.get('amount', 0),
        'device_velocity': txn_data.get('device_velocity', 0),
        'ip_country_match': txn_data.get('ip_country_match', 1),
        'time_since_last_txn': txn_data.get('time_since_last_txn', 100)
    }], columns=FEATURE_COLUMNS)
    
    prediction = clf.predict(features)[0]
    probabilities = clf.predict_proba(features)[0]
    
    if len(probabilities) > 1:
        fraud_prob = round(probabilities[1] * 100, 2)
    else:
        fraud_prob = 0.0 if prediction == 0 else 100.0
    
    # Explainable AI: SHAP values
    shap_values = explainer.shap_values(features)
    
    # For RandomForestClassifier, shap_values is a list of arrays (one for each class)
    # We want the explanation for the positive class (class 1: fraud)
    if isinstance(shap_values, list) and len(shap_values) > 1:
        shap_vals_fraud = shap_values[1][0]
    else:
        # In newer shap versions, it might just be the array if output_names are handled differently
        shap_vals_fraud = shap_values[0] if len(shap_values.shape) == 2 else shap_values[0,:,1] if len(shap_values.shape) > 2 else shap_values[0]
        if isinstance(shap_vals_fraud, (list, np.ndarray)) and len(shap_vals_fraud) > 0 and isinstance(shap_vals_fraud[0], (list, np.ndarray)):
            shap_vals_fraud = shap_values[0][1] if len(shap_values) > 0 else shap_values[0]

    # Normalize SHAP values to percentages to show contribution
    # We only care about positive contributions pushing towards fraud
    total_positive_shap = sum([v for v in shap_vals_fraud if v > 0])
    
    xai_reasons = []
    if total_positive_shap > 0 and prediction == 1:
        for fname, s_val in zip(FEATURE_COLUMNS, shap_vals_fraud):
            if s_val > 0:
                contribution = (s_val / total_positive_shap) * 100
                if contribution > 5.0: # Only report significant factors
                    val = features[fname].iloc[0]
                    xai_reasons.append(f"{fname.replace('_', ' ').title()} ({contribution:.1f}%)")
    
    reason_str = ""
    if prediction:
        if xai_reasons:
            reason_str = f"Blocked by AI ({fraud_prob}% fraud risk). Key Drivers: " + ", ".join(xai_reasons) + "."
        else:
            reason_str = f"Blocked by AI ({fraud_prob}% fraud risk) based on complex non-linear pattern match."
    else:
        reason_str = "Transaction matches normal baseline behavior. Allowed."
    
    return {
        "is_fraud": bool(prediction),
        "fraud_probability": fraud_prob,
        "action": "BLOCK" if prediction else "ALLOW",
        "reason": reason_str,
        "xai_flags": xai_reasons if prediction else []
    }
