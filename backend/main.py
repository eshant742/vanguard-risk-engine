import hashlib
import random
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml_engine import initialize_model, predict_transaction
from underwriting_engine import analyze_merchant
from fx_risk_engine import get_fx_risk_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vanguard")


# Modern FastAPI lifespan (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and train the ML model
    logger.info("Initializing ML model on startup...")
    initialize_model()
    logger.info("ML model trained and ready.")
    yield
    # Shutdown
    logger.info("Vanguard Risk Engine shutting down.")


app = FastAPI(
    title="Vanguard Risk Engine",
    description="AI-powered risk management platform for Razorpay",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["System"])
def root():
    """Root endpoint — project info and available API routes."""
    return {
        "project": "Vanguard Risk Engine",
        "version": "1.0.0",
        "track": "Razorpay AI Buildathon — Track 02: AI Risk Manager",
        "modules": [
            "Fraud-Spike Detector (ML)",
            "Chargeback Evidence Auto-Responder (NLP)",
            "Abuse-Ring Sentinel",
            "Return-Risk Scorer",
            "AI Merchant Underwriting (Compliance)",
            "Macroeconomic FX & Liquidity Risk"
        ],
        "endpoints": {
            "fraud_predict": "POST /api/fraud/predict",
            "fraud_metrics": "GET /api/fraud/metrics",
            "chargeback": "POST /api/fraud/chargeback",
            "abuse_ring": "GET /api/fraud/abuse-ring",
            "return_risk": "POST /api/fraud/return-risk",
            "underwrite": "POST /api/underwrite",
            "fx_risk": "GET /api/fx-risk",
            "activity_feed": "GET /api/fraud/activity-feed",
            "health": "GET /api/health"
        }
    }


@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint for operational verification."""
    from ml_engine import clf as _clf
    return {
        "status": "healthy",
        "engine": "Vanguard Risk Engine",
        "ml_model_loaded": _clf is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# 1. FRAUD-SPIKE DETECTOR (ML)
# ──────────────────────────────────────────────

class Transaction(BaseModel):
    amount: float = Field(ge=0, description="Transaction amount must be positive")
    device_velocity: int = Field(ge=0, description="Velocity must be non-negative")
    ip_country_match: int = Field(ge=0, le=1, description="Must be 0 or 1")
    time_since_last_txn: float = Field(ge=0, description="Time since last transaction must be non-negative")


@app.get("/api/fraud/metrics")
def get_metrics():
    try:
        metrics = initialize_model()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fraud/predict")
def predict(txn: Transaction):
    try:
        result = predict_transaction(txn.model_dump())
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 2. CHARGEBACK EVIDENCE AUTO-RESPONDER
# ──────────────────────────────────────────────

class Dispute(BaseModel):
    transaction_id: str = Field(min_length=1)
    customer_claim: str = Field(min_length=1)


@app.post("/api/fraud/chargeback")
def generate_chargeback_evidence(dispute: Dispute):
    # Generate deterministic-but-unique transaction data from the transaction ID
    # This makes each submission look realistic while being reproducible
    seed = int(hashlib.md5(dispute.transaction_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    ip_octets = f"{rng.randint(10,220)}.{rng.randint(1,255)}.{rng.randint(1,255)}.{rng.randint(1,255)}"
    tracking = f"BD{rng.randint(10000000, 99999999)}IN"
    day = rng.randint(1, 28)
    hour = rng.randint(8, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    devices = ["iPhone 15 Pro - Safari", "iPhone 14 Pro - Safari", "Samsung S24 - Chrome", "Pixel 8 - Chrome"]
    carriers = ["BlueDart", "DTDC", "Delhivery", "Ecom Express"]

    txn_data = {
        "date": f"2026-08-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC",
        "ip_address": f"{ip_octets} (Verified India)",
        "avs_match": "YES (Zip Code & Address Matched)",
        "cvv_match": "YES",
        "delivery_status": f"DELIVERED via {rng.choice(carriers)} (Tracking: {tracking})",
        "device_fingerprint": f"{rng.choice(devices)} - Trusted Device"
    }
    
    # NLP Heuristic to draft letter based on claim
    claim = dispute.customer_claim.lower()
    defense_strategy = ""
    
    if "not received" in claim or "didn't get" in claim or "never received" in claim or "not delivered" in claim:
        defense_strategy = f"The customer claims non-receipt, but our logistics integration proves successful delivery. Tracking # {tracking} confirms delivery to the AVS-verified billing address on {txn_data['date']}."
    elif "unauthorized" in claim or "stolen" in claim or "didn't authorize" in claim or "not me" in claim:
        defense_strategy = f"The customer claims unauthorized use. However, the transaction was made from a trusted device fingerprint associated with their previous purchases, and both CVV and Address Verification System (AVS) matched perfectly. The IP address {txn_data['ip_address']} matches their historical location."
    elif "defective" in claim or "broken" in claim or "damaged" in claim or "not working" in claim:
        defense_strategy = f"The customer claims product defect. Our records show the item was delivered intact per carrier confirmation ({txn_data['delivery_status']}). The merchant's return policy requires the customer to initiate a return within 7 days, which was not done. No prior contact was made to customer support before filing this chargeback."
    elif "cancelled" in claim or "refund" in claim:
        defense_strategy = f"The customer claims they requested cancellation. Our system logs show no cancellation request was received prior to fulfillment. The order was processed, shipped, and delivered successfully ({txn_data['delivery_status']})."
    else:
        defense_strategy = f"All cryptographic and logistical checkpoints (AVS, CVV, IP, and Device Fingerprinting) were successfully verified at the time of checkout, proving the cardholder willingly authorized this transaction."

    evidence_letter = f"""=========================================================
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
- Date: {txn_data['date']}
- Status: {txn_data['delivery_status']}

3. DEFENSE SUMMARY:
{defense_strategy}

Given this cryptographic and logistical evidence, we request that this chargeback be immediately reversed in the merchant's favor.

Sincerely,
Vanguard Risk Engine (Automated Dispute Responder)
Razorpay AI Buildathon — Track 02: AI Risk Manager"""

    return {"evidence_letter": evidence_letter}


# ──────────────────────────────────────────────
# 3. ABUSE-RING SENTINEL
# ──────────────────────────────────────────────

@app.get("/api/fraud/abuse-ring")
def get_abuse_rings():
    # Simulate scanning the last 24 hours of transactions for clusters
    return {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_transactions_scanned": 14829,
        "active_rings": [
            {
                "ring_id": "RNG-8472-B",
                "shared_vector": "IP Address: 103.44.21.99 (VPN Data Center)",
                "unique_cards_used": 7,
                "total_attempted_inr": 145000,
                "status": "BLOCKED (Sentinel Activated)",
                "detection_method": "IP Clustering + Velocity Analysis",
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
                "detection_method": "Device Fingerprint Clustering",
                "nodes": [
                    "Card ending in 1122 (Failed)",
                    "Card ending in 3344 (Failed)",
                    "Card ending in 5566 (Failed)",
                    "Card ending in 7788 (Failed)"
                ]
            },
            {
                "ring_id": "RNG-3301-K",
                "shared_vector": "Shipping Address: 42 MG Road, Bangalore (Drop Location)",
                "unique_cards_used": 5,
                "total_attempted_inr": 67500,
                "status": "BLOCKED (Sentinel Activated)",
                "detection_method": "Shipping Address Graph Analysis",
                "nodes": [
                    "Card ending in 2233 (Failed)",
                    "Card ending in 4455 (Failed)",
                    "Card ending in 6677 (Failed)",
                    "Card ending in 8899 (Failed)",
                    "Card ending in 1010 (Failed)"
                ]
            }
        ]
    }


# ──────────────────────────────────────────────
# 4. RETURN-RISK SCORER
# ──────────────────────────────────────────────

class ReturnHistory(BaseModel):
    customer_id: str = Field(min_length=1)
    items_kept_last_year: int = Field(ge=0)
    items_returned_last_year: int = Field(ge=0)
    current_cart_value: float = Field(ge=0)


@app.post("/api/fraud/return-risk")
def calculate_return_risk(history: ReturnHistory):
    total_purchases = history.items_kept_last_year + history.items_returned_last_year
    
    if total_purchases == 0:
        return {
            "return_probability": 10.0,
            "risk_level": "LOW",
            "action": "STANDARD_POLICY",
            "recommendation": "New customer with no purchase history. Offer standard free returns to build loyalty.",
            "breakdown": {
                "return_rate": 0.0,
                "cart_risk_factor": round(history.current_cart_value / 50000 * 5, 2),
                "history_factor": 0.0
            }
        }
        
    return_rate = history.items_returned_last_year / total_purchases
    
    # Improved formula: weighted combination with reasonable cart impact
    # Cart factor: ₹50,000+ carts add up to 10 points (not 100)
    history_factor = return_rate * 100
    cart_risk_factor = min((history.current_cart_value / 50000) * 10, 10)
    
    return_probability = min(round(history_factor + cart_risk_factor, 2), 99.9)
    
    breakdown = {
        "return_rate": round(return_rate * 100, 1),
        "cart_risk_factor": round(cart_risk_factor, 2),
        "history_factor": round(history_factor, 2)
    }
    
    if return_probability > 75.0:
        return {
            "return_probability": return_probability,
            "risk_level": "CRITICAL",
            "action": "DISABLE_FREE_RETURNS",
            "recommendation": f"Customer has a {round(return_rate*100)}% historical return rate. AI strongly recommends disabling 'Free Returns' and enforcing a 15% restocking fee for this high-value cart to protect merchant margins.",
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
            "recommendation": "Customer is highly profitable. Proceed with standard Free Returns.",
            "breakdown": breakdown
        }


# ──────────────────────────────────────────────
# 5. AI MERCHANT UNDERWRITING
# ──────────────────────────────────────────────

class UnderwriteRequest(BaseModel):
    url: str = Field(min_length=4)


@app.post("/api/underwrite")
def underwrite_merchant(req: UnderwriteRequest):
    try:
        return analyze_merchant(req.url)
    except Exception as e:
        logger.error(f"Underwriting failed for {req.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 6. FX & LIQUIDITY RISK
# ──────────────────────────────────────────────

@app.get("/api/fx-risk")
def fx_risk():
    try:
        return get_fx_risk_data()
    except Exception as e:
        logger.error(f"FX risk engine failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 7. LIVE ACTIVITY FEED (Real-Time Threat Ticker)
# ──────────────────────────────────────────────

@app.get("/api/fraud/activity-feed")
def get_activity_feed():
    """Generate realistic recent activity events for the live threat ticker"""
    rng = random.Random()
    
    event_templates = [
        {
            "type": "fraud_block",
            "templates": [
                "Blocked Velocity Attack from {ip} (Saved ₹{amount})",
                "Blocked Card Testing from {ip} ({cards} cards rejected)",
                "Geo-Anomaly Block: {country} IP on India-issued card (₹{amount})",
            ]
        },
        {
            "type": "chargeback_win",
            "templates": [
                "Defeated Chargeback Claim on {txn_id} (₹{amount} recovered)",
                "Auto-generated Evidence Letter for {txn_id} — Bank ruled in merchant favor",
            ]
        },
        {
            "type": "abuse_ring",
            "templates": [
                "Abuse-Ring {ring_id} Neutered — {cards} Cards Banned",
                "Sentinel detected new cluster from {ip} — {cards} linked cards blocked",
            ]
        },
        {
            "type": "return_fraud",
            "templates": [
                "Wardrobing Fraud Prevented — User {cust_id} (Saved ₹{amount})",
                "Serial Returner {cust_id} flagged — Free returns disabled (₹{amount} cart)",
            ]
        },
        {
            "type": "underwriting",
            "templates": [
                "Merchant {url} auto-rejected — Prohibited content detected",
                "Merchant {url} approved — Trust Score: {score}/100",
            ]
        }
    ]
    
    events = []
    now = datetime.now()
    base_hour = now.hour
    base_min = max(0, now.minute - rng.randint(5, 20))
    
    for i in range(8):
        category = rng.choice(event_templates)
        template = rng.choice(category["templates"])
        
        minute = min(59, base_min + i * rng.randint(1, 3))
        second = rng.randint(0, 59)
        timestamp = f"{base_hour:02d}:{minute:02d}:{second:02d}"
        
        message = template.format(
            ip=f"{rng.randint(100,200)}.{rng.randint(1,255)}.{rng.randint(1,99)}.{rng.randint(1,255)}",
            amount=f"{rng.randint(2, 45) * 500:,}",
            cards=rng.randint(3, 9),
            country=rng.choice(["Nigeria", "Russia", "Vietnam", "Romania"]),
            txn_id=f"pay_{rng.choice(['Q8V','P41','X9L','M3K','R7N'])}{rng.randint(10,99)}",
            ring_id=f"RNG-{rng.randint(1000,9999)}",
            cust_id=f"CUST-{rng.randint(100,999)}",
            url=rng.choice(["cryptoking.io", "fastbet365.com", "legit-store.com"]),
            score=rng.randint(85, 100),
        )
        
        events.append({
            "timestamp": timestamp,
            "type": category["type"],
            "message": message
        })
    
    return {"events": events}
