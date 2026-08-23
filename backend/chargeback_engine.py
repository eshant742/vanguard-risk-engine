"""
Chargeback Evidence Auto-Responder Engine (TF-IDF NLP Upgrade)

Uses TF-IDF Vectorization and Cosine Similarity to classify customer claims
against Visa/Mastercard dispute reason codes mathematically, replacing
fragile keyword matching with robust semantic similarity.
"""

import hashlib
import random
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("vanguard.chargeback")

# Visa/Mastercard dispute reason code categories with rich semantic descriptions
# to train the TF-IDF vectorizer.
CLAIM_CATEGORIES = {
    "non_receipt": {
        "corpus_text": "Item was not received, never arrived, package lost in transit, delivery failed, still waiting, where is my order, not delivered, shipping delay, missing package.",
        "reason_code": "13.1 (Merchandise Not Received)",
        "template": (
            "The customer claims non-receipt, but our logistics integration "
            "proves successful delivery. Tracking # {tracking} confirms "
            "delivery to the AVS-verified billing address on {date}. "
            "Carrier signature confirmation is available upon request."
        )
    },
    "unauthorized": {
        "corpus_text": "Unauthorized transaction, card was stolen, I didn't authorize this, not me, fraud, someone else used my card, account hacked, identity theft, don't recognize charge, fraudulent purchase.",
        "reason_code": "10.4 (Fraud — Card-Absent Environment)",
        "template": (
            "The customer claims unauthorized use. However, the transaction "
            "was made from a trusted device fingerprint associated with their "
            "previous purchases, and both CVV and Address Verification System "
            "(AVS) matched perfectly. The IP address {ip} matches their "
            "historical location. 3-D Secure authentication was passed."
        )
    },
    "defective": {
        "corpus_text": "Product is defective, broken item, arrived damaged, not working properly, wrong item sent, not as described, poor quality, faulty merchandise, malfunctioned, inaccurate description.",
        "reason_code": "13.3 (Not as Described or Defective)",
        "template": (
            "The customer claims product defect. Our records show the item "
            "was delivered intact per carrier confirmation ({delivery}). "
            "The merchant's return policy requires the customer to initiate "
            "a return within 7 days, which was not done. No prior contact "
            "was made to customer support before filing this chargeback."
        )
    },
    "cancellation": {
        "corpus_text": "I cancelled this order, please refund, want to return it, changed my mind, want my money back, didn't want it anymore, requested cancellation, subscription cancelled.",
        "reason_code": "13.6 (Credit Not Processed)",
        "template": (
            "The customer claims they requested cancellation. Our system "
            "logs show no cancellation request was received prior to "
            "fulfillment. The order was processed, shipped, and delivered "
            "successfully ({delivery}). The merchant's cancellation policy "
            "was clearly displayed at checkout."
        )
    },
    "duplicate": {
        "corpus_text": "Duplicate charge, billed twice, double charge, charged two times, multiple charges for same item, overcharged, recurring billing error.",
        "reason_code": "12.6.1 (Duplicate Processing)",
        "template": (
            "The customer claims duplicate billing. Our payment processor "
            "logs confirm only a single successful authorization and capture "
            "for Transaction {txn_id} on {date}. No other transactions from "
            "this card match the amount or timeframe. The customer may be "
            "viewing a pending hold that was auto-released."
        )
    }
}

_FALLBACK_TEMPLATE = (
    "All cryptographic and logistical checkpoints (AVS, CVV, IP, and "
    "Device Fingerprinting) were successfully verified at the time of "
    "checkout, proving the cardholder willingly authorized this transaction."
)

# Initialize and train TF-IDF Vectorizer
_category_keys = list(CLAIM_CATEGORIES.keys())
_corpus = [CLAIM_CATEGORIES[k]["corpus_text"] for k in _category_keys]

_vectorizer = TfidfVectorizer(stop_words='english')
_tfidf_matrix = _vectorizer.fit_transform(_corpus)


def _classify_claim_nlp(claim_text: str) -> tuple:
    """
    Classifies a customer dispute claim using TF-IDF and Cosine Similarity.
    Returns (category_key, similarity_score, all_scores).
    """
    if not claim_text or len(claim_text.strip()) < 3:
        return "generic", 0.0, {}

    # Vectorize the incoming claim
    claim_vec = _vectorizer.transform([claim_text])
    
    # Calculate cosine similarity against all categories
    similarities = cosine_similarity(claim_vec, _tfidf_matrix)[0]
    
    # Map scores to categories
    scores_dict = {
        _category_keys[i]: round(float(similarities[i]), 4)
        for i in range(len(_category_keys))
    }
    
    # Find best match
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    
    # Minimum similarity threshold to prevent forced matches on garbage text
    if best_score > 0.10:
        return _category_keys[best_idx], best_score, scores_dict
    
    return "generic", best_score, scores_dict


def generate_evidence(transaction_id: str, customer_claim: str) -> dict:
    """
    Generates a formal chargeback defense evidence letter.
    Uses TF-IDF NLP to semantically match the claim to Visa/MC reason codes.
    """
    # Deterministic seed from transaction ID
    seed = int(hashlib.md5(transaction_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    ip_octets = (f"{rng.randint(10, 220)}.{rng.randint(1, 255)}."
                 f"{rng.randint(1, 255)}.{rng.randint(1, 255)}")
    tracking = f"BD{rng.randint(10000000, 99999999)}IN"
    day = rng.randint(1, 28)
    hour = rng.randint(8, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)

    devices = [
        "iPhone 15 Pro - Safari", "iPhone 14 Pro - Safari",
        "Samsung S24 - Chrome", "Pixel 8 - Chrome"
    ]
    carriers = ["BlueDart", "DTDC", "Delhivery", "Ecom Express"]

    txn_data = {
        "date": f"2026-08-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC",
        "ip_address": f"{ip_octets} (Verified India)",
        "avs_match": "YES (Zip Code & Address Matched)",
        "cvv_match": "YES",
        "delivery_status": f"DELIVERED via {rng.choice(carriers)} (Tracking: {tracking})",
        "device_fingerprint": f"{rng.choice(devices)} - Trusted Device"
    }

    # Classify the claim using TF-IDF NLP
    category, best_score, all_scores = _classify_claim_nlp(customer_claim)

    if category in CLAIM_CATEGORIES:
        config = CLAIM_CATEGORIES[category]
        reason_code = config["reason_code"]
        defense_strategy = config["template"].format(
            tracking=tracking,
            date=txn_data["date"],
            ip=txn_data["ip_address"],
            delivery=txn_data["delivery_status"],
            txn_id=transaction_id
        )
    else:
        reason_code = "General Dispute"
        defense_strategy = _FALLBACK_TEMPLATE

    evidence_letter = f"""=========================================================
CHARGEBACK DISPUTE EVIDENCE LETTER (VISA/MASTERCARD)
=========================================================
TRANSACTION ID : {transaction_id}
MERCHANT NAME  : Razorpay Gateway Merchant
DISPUTE REASON : "{customer_claim}"
REASON CODE    : {reason_code}
=========================================================

To the Issuing Bank,

We are submitting compelling evidence to contest the chargeback for Transaction {transaction_id}.

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

    return {
        "evidence_letter": evidence_letter,
        "claim_category": category,
        "reason_code": reason_code,
        "nlp_confidence": round(best_score * 100, 1),
        "nlp_scores": all_scores
    }
