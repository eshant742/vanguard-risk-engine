from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ml_engine import initialize_model, predict_transaction

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Transaction(BaseModel):
    amount: float
    device_velocity: int
    ip_country_match: int
    time_since_last_txn: float

@app.on_event("startup")
def startup_event():
    # Initialize and train the ML model on startup
    initialize_model()

@app.get("/api/fraud/metrics")
def get_metrics():
    try:
        metrics = initialize_model()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fraud/predict")
def predict(txn: Transaction):
    try:
        result = predict_transaction(txn.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class Dispute(BaseModel):
    transaction_id: str
    customer_claim: str

@app.post("/api/fraud/chargeback")
def generate_chargeback_evidence(dispute: Dispute):
    # Mock pulling transaction data from database
    txn_data = {
        "date": "2026-08-15 14:30:22 UTC",
        "ip_address": "49.36.211.14 (Verified India)",
        "avs_match": "YES (Zip Code & Address Matched)",
        "cvv_match": "YES",
        "delivery_status": "DELIVERED via BlueDart (Tracking: BD88992011IN)",
        "device_fingerprint": "iPhone 14 Pro - Safari - Trusted Device"
    }
    
    # NLP Heuristic to draft letter based on claim
    claim = dispute.customer_claim.lower()
    defense_strategy = ""
    
    if "not received" in claim or "didn't get" in claim:
        defense_strategy = f"The customer claims non-receipt, but our logistics integration proves successful delivery. Tracking # BD88992011IN confirms delivery to the AVS-verified billing address."
    elif "unauthorized" in claim or "stolen" in claim:
        defense_strategy = f"The customer claims unauthorized use. However, the transaction was made from a trusted device fingerprint associated with their previous purchases, and both CVV and Address Verification System (AVS) matched perfectly. The IP address {txn_data['ip_address']} matches their historical location."
    else:
        defense_strategy = f"All cryptographic and logistical checkpoints (AVS, CVV, IP, and Device Fingerprinting) were successfully verified at the time of checkout, proving the cardholder willingly authorized this transaction."

    evidence_letter = f"""
=========================================================
CHARGEBACK DISPUTE EVIDENCE LETTER (VISA/MASTERCARD)
=========================================================
TRANSACTION ID : {dispute.transaction_id}
MERCHANT NAME  : Razorpay Gateway Merchant
DISPUTE REASON : "{dispute.customer_claim}"
=========================================================

To the Issuing Bank,

We are submitting compelling evidence to contest the chargeback for Transaction {dispute.transaction_id}.

1. AUTHORIZATION PROOF:
- AVS Match: {txn_data['avs_match']}
- CVV Match: {txn_data['cvv_match']}
- IP Address: {txn_data['ip_address']}
- Device ID: {txn_data['device_fingerprint']}

2. FULFILLMENT PROOF:
- Status: {txn_data['delivery_status']}

DEFENSE SUMMARY:
{defense_strategy}

Given this cryptographic and logistical evidence, we request that this chargeback be immediately reversed in the merchant's favor.

Sincerely,
Vanguard Risk Engine (Automated Dispute Responder)
"""
    return {"evidence_letter": evidence_letter}

@app.get("/api/fraud/abuse-ring")
def get_abuse_rings():
    # Simulate scanning the last 24 hours of transactions for clusters
    return {
        "active_rings": [
            {
                "ring_id": "RNG-8472-B",
                "shared_vector": "IP Address: 103.44.21.99 (VPN Data Center)",
                "unique_cards_used": 7,
                "total_attempted_inr": 145000,
                "status": "BLOCKED (Sentinel Activated)",
                "nodes": [
                    "Card ending in 4412 (Failed)",
                    "Card ending in 9921 (Failed)",
                    "Card ending in 1184 (Failed)",
                    "Card ending in 7733 (Failed)",
                    "Card ending in 2291 (Failed)",
                    "Card ending in 5544 (Failed)",
                    "Card ending in 8811 (Failed)"
                ]
            },
            {
                "ring_id": "RNG-9910-X",
                "shared_vector": "Device Fingerprint: Hash-99A1B2 (Android Emulator)",
                "unique_cards_used": 4,
                "total_attempted_inr": 82000,
                "status": "BLOCKED (Sentinel Activated)",
                "nodes": [
                    "Card ending in 1122 (Failed)",
                    "Card ending in 3344 (Failed)",
                    "Card ending in 5566 (Failed)",
                    "Card ending in 7788 (Failed)"
                ]
            }
        ]
    }

class ReturnHistory(BaseModel):
    customer_id: str
    items_kept_last_year: int
    items_returned_last_year: int
    current_cart_value: float

@app.post("/api/fraud/return-risk")
def calculate_return_risk(history: ReturnHistory):
    total_purchases = history.items_kept_last_year + history.items_returned_last_year
    
    if total_purchases == 0:
        return {
            "return_probability": 10.0,
            "risk_level": "LOW",
            "action": "STANDARD_POLICY",
            "recommendation": "New customer. Offer standard free returns to build loyalty."
        }
        
    return_rate = history.items_returned_last_year / total_purchases
    return_probability = min(round((return_rate * 100) + (history.current_cart_value / 5000), 2), 99.9)
    
    if return_probability > 75.0:
        return {
            "return_probability": return_probability,
            "risk_level": "CRITICAL",
            "action": "DISABLE_FREE_RETURNS",
            "recommendation": f"Customer has a {round(return_rate*100)}% historical return rate. AI strongly recommends disabling 'Free Returns' and enforcing a 15% restocking fee for this high-value cart to protect merchant margins."
        }
    elif return_probability > 40.0:
        return {
            "return_probability": return_probability,
            "risk_level": "MEDIUM",
            "action": "WARNING_PROMPT",
            "recommendation": "Customer has moderate return risk. Show a warning at checkout that returns must be in original packaging with tags attached."
        }
    else:
        return {
            "return_probability": return_probability,
            "risk_level": "LOW",
            "action": "STANDARD_POLICY",
            "recommendation": "Customer is highly profitable. Proceed with standard Free Returns."
        }

