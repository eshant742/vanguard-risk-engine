"""
Return-Risk Scorer Engine (Wardrobing Fraud NLP Upgrade)

Calculates the risk of wardrobing fraud using a Logistic Regression model
trained on synthetic customer return histories, replacing the legacy
hardcoded formula with genuine Machine Learning.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("vanguard.return_risk")

_model = None
_scaler = None

def _initialize_model():
    """
    Generates synthetic purchase history data and trains a Logistic Regression
    model to predict the probability of a return.
    """
    global _model, _scaler
    np.random.seed(42)
    
    n_samples = 2000
    # Features
    items_kept = np.random.poisson(lam=5, size=n_samples)
    items_returned = np.random.poisson(lam=2, size=n_samples)
    cart_values = np.random.exponential(scale=10000, size=n_samples)
    
    # Calculate historical return rate (avoid div by zero)
    total_items = items_kept + items_returned
    # Use np.divide with 'where' to avoid RuntimeWarning on division by zero
    return_rate = np.divide(items_returned, total_items, out=np.zeros_like(total_items, dtype=float), where=total_items > 0)
    
    # Target: 1 if this cart will be returned, 0 if kept
    # Higher return rate + high cart value increases likelihood of return
    z = -3.0 + (return_rate * 6.0) + (cart_values / 50000 * 2.0)
    # Sigmoid to get probability
    prob = 1 / (1 + np.exp(-z))
    y = np.random.binomial(1, prob)
    
    X = pd.DataFrame({
        'items_kept': items_kept,
        'items_returned': items_returned,
        'cart_value': cart_values
    })
    
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)
    
    _model = LogisticRegression(random_state=42, class_weight='balanced')
    _model.fit(X_scaled, y)
    
    logger.info("Return Risk Logistic Regression model initialized.")

def calculate_return_risk_score(
        items_kept_last_year: int,
        items_returned_last_year: int,
        current_cart_value: float) -> Dict[str, Any]:
    """
    Calculates return risk probability and returns a decision payload
    using Logistic Regression.
    """
    global _model, _scaler
    if _model is None:
        _initialize_model()

    # Prepare features
    features = pd.DataFrame([{
        'items_kept': items_kept_last_year,
        'items_returned': items_returned_last_year,
        'cart_value': current_cart_value
    }])
    
    features_scaled = _scaler.transform(features)
    
    # Predict probability
    prob_class_1 = _model.predict_proba(features_scaled)[0][1]
    
    # Extract coefficients for explainability
    coeffs = _model.coef_[0]
    
    # Map probability to 0-99.9%
    return_probability = min(round(prob_class_1 * 100, 2), 99.9)
    
    total_purchases = items_kept_last_year + items_returned_last_year
    historical_rate = (items_returned_last_year / total_purchases * 100) if total_purchases > 0 else 0.0

    breakdown = {
        "return_rate": round(historical_rate, 1),
        "history_factor": round(float(coeffs[1] * features_scaled[0][1]), 2), # Items returned factor
        "cart_risk_factor": round(float(coeffs[2] * features_scaled[0][2]), 2) # Cart value factor
    }

    if return_probability > 75.0:
        return {
            "return_probability": return_probability,
            "risk_level": "CRITICAL",
            "action": "DISABLE_FREE_RETURNS",
            "recommendation": f"Customer has a {round(historical_rate)}% historical return rate. AI strongly recommends disabling 'Free Returns' and enforcing a 15% restocking fee for this high-value cart to protect merchant margins.",
            "breakdown": breakdown
        }
    elif return_probability > 40.0:
        return {
            "return_probability": return_probability,
            "risk_level": "MEDIUM",
            "action": "WARNING_PROMPT",
            "recommendation": "Customer has moderate return risk. Show a warning at checkout that returns must be in original packaging with tags attached.",
            "breakdown": breakdown
        }
    else:
        return {
            "return_probability": return_probability,
            "risk_level": "LOW",
            "action": "STANDARD_POLICY",
            "recommendation": "Customer is highly profitable or risk is minimal. Proceed with standard Free Returns.",
            "breakdown": breakdown
        }
