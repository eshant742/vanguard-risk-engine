import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, confusion_matrix

# 1. Generate Synthetic Merchant Transactions
def generate_synthetic_data(n_samples=2000):
    np.random.seed(42)
    
    # Features:
    # amount: transaction amount in INR
    # device_velocity: number of txns from this device in the last hour
    # ip_country_match: 1 if IP matches card issuing country, 0 if mismatch
    # time_since_last_txn: minutes since last transaction for this user
    
    amounts = np.random.exponential(scale=2000, size=n_samples) # Normal txns
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
        # Lowered threshold from >4 to >2.5 to ensure ~15-20% fraud rate
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
metrics_cache = None

def initialize_model():
    global clf, metrics_cache
    if clf is not None:
        return metrics_cache
        
    df = generate_synthetic_data()
    
    X = df[['amount', 'device_velocity', 'ip_country_match', 'time_since_last_txn']]
    y = df['is_fraud']
    
    # Strictly follow Razorpay rule: "held-out test set"
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    # Train model
    clf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
    clf.fit(X_train, y_train)
    
    # Evaluate on held-out test set
    y_pred = clf.predict(X_test)
    
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    # Calculate Financial Impact Metrics
    false_positives = int(cm[0][1])
    true_positives = int(cm[1][1])
    
    # Cost assumptions for Buildathon metrics
    # CLV lost per false positive = ₹2000
    # Average fraud transaction value protected = ₹4500 (based on synthetic generation > 3000 rule)
    total_false_positive_cost = false_positives * 2000
    total_fraud_prevented_value = true_positives * 4500
    net_margin_protected = total_fraud_prevented_value - total_false_positive_cost
    
    metrics_cache = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positives": false_positives,
        "true_positives": true_positives,
        "false_negatives": int(cm[1][0]),
        "true_negatives": int(cm[0][0]),
        "false_positive_cost_inr": total_false_positive_cost,
        "total_fraud_prevented_inr": total_fraud_prevented_value,
        "net_margin_protected_inr": net_margin_protected,
        "test_set_size": len(y_test)
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
    }])
    
    prediction = clf.predict(features)[0]
    probabilities = clf.predict_proba(features)[0]
    
    fraud_prob = round(probabilities[1] * 100, 2)
    
    # Explainable AI (XAI) feature contribution heuristic
    xai_reasons = []
    if txn_data.get('device_velocity', 0) > 2:
        xai_reasons.append(f"High Device Velocity ({txn_data.get('device_velocity')} txns/hr)")
    if txn_data.get('ip_country_match', 1) == 0:
        xai_reasons.append("IP Country Mismatch")
    if txn_data.get('amount', 0) > 3000:
        xai_reasons.append(f"High Amount (₹{txn_data.get('amount')})")
    if txn_data.get('time_since_last_txn', 100) < 5:
        xai_reasons.append("Rapid Successive Transaction (<5 mins)")
        
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
