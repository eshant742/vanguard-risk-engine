import logging
from datetime import datetime, timezone, timedelta
import random
from contextlib import asynccontextmanager
import ipaddress
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import all Engine Modules
from ml_engine import initialize_model, predict_transaction
from underwriting_engine import analyze_merchant
from fx_risk_engine import get_fx_risk_data
from chargeback_engine import generate_evidence
from abuse_ring_engine import scan_abuse_rings
from return_risk_engine import calculate_return_risk_score

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

# BUG FIX: CORS middleware must be added before routes and with specific origins
# when allow_credentials=True is used to prevent security vulnerabilities.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
def chargeback_endpoint(dispute: Dispute):
    try:
        return generate_evidence(dispute.transaction_id, dispute.customer_claim)
    except Exception as e:
        logger.error(f"Chargeback generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 3. ABUSE-RING SENTINEL
# ──────────────────────────────────────────────

@app.get("/api/fraud/abuse-ring")
def get_abuse_rings():
    """
    Returns detected fraud rings discovered via Graph Analysis.
    """
    try:
        return scan_abuse_rings()
    except Exception as e:
        logger.error(f"Abuse ring scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 4. RETURN-RISK SCORER
# ──────────────────────────────────────────────

class ReturnHistory(BaseModel):
    customer_id: str = Field(min_length=1)
    items_kept_last_year: int = Field(ge=0)
    items_returned_last_year: int = Field(ge=0)
    current_cart_value: float = Field(ge=0)


@app.post("/api/fraud/return-risk")
def return_risk_endpoint(history: ReturnHistory):
    try:
        logger.info(f"Return risk check for customer: {history.customer_id}")
        return calculate_return_risk_score(
            history.items_kept_last_year,
            history.items_returned_last_year,
            history.current_cart_value
        )
    except Exception as e:
        logger.error(f"Return risk calculation failed for {history.customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# 5. AI MERCHANT UNDERWRITING
# ──────────────────────────────────────────────

class UnderwriteRequest(BaseModel):
    url: str = Field(min_length=4)


@app.post("/api/underwrite")
def underwrite_merchant(req: UnderwriteRequest):
    try:
        # SSRF Protection: reject URLs pointing to private/internal IP ranges
        parsed = urlparse(req.url if req.url.startswith("http") else f"https://{req.url}")
        hostname = parsed.hostname or ""
        if hostname:
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_reserved:
                    raise HTTPException(
                        status_code=400,
                        detail=f"URL points to a private/internal IP address ({hostname}). This is not allowed."
                    )
            except ValueError:
                # hostname is a domain name, not an IP — that's normal and fine
                pass
        return analyze_merchant(req.url)
    except HTTPException:
        raise
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
    
    # Generate timestamps going BACKWARD from now for realism
    # Start at current time and subtract increasing offsets
    cumulative_offset_seconds = rng.randint(30, 120)  # First event is 30-120 seconds ago
    
    for i in range(8):
        category = rng.choice(event_templates)
        template = rng.choice(category["templates"])
        
        event_time = now - timedelta(seconds=cumulative_offset_seconds)
        timestamp = event_time.strftime("%H:%M:%S")
        
        # Increase offset for next (older) event
        cumulative_offset_seconds += rng.randint(60, 300)
        
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
    
    # Events are most recent first; reverse for chronological order
    events.reverse()
    
    return {"events": events}
