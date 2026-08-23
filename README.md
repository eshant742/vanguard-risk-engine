# Vanguard Risk Engine

**Razorpay AI Builder Internship 2026 — Track 02: AI Risk Manager**

Vanguard is a unified, autonomous Risk Management platform that acts as a comprehensive defense system for Razorpay merchants. It tackles six distinct classes of financial loss (Fraud, Chargebacks, Abuse Rings, Returns, Compliance, and FX Volatility) using a mix of Machine Learning (Random Forests), NLP (VADER Sentiment Analysis), and real-time streaming data.

## 🚀 How It Meets The Bar (Track 02 Requirements)

1. **"Build a working detector... with measured precision and recall on a held-out test set."**
   - The **Fraud-Spike Detector** uses a Random Forest Classifier trained on synthetic data.
   - The **ML Metrics Dashboard** displays Precision, Recall, F1 Score, and ROC-AUC specifically calculated on a strict 20% held-out test set.
   
2. **"Honest metrics including false-positive cost."**
   - We explicitly calculate the **Net Margin Protected** by subtracting the total Customer Lifetime Value (CLV) lost to False Positives from the total fraud value successfully blocked.
   
3. **"Strictly defense-only."**
   - Every module is purely defensive (blocking transactions, drafting defense evidence, identifying existing abuse rings, managing macro-liquidity).

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VANGUARD RISK ENGINE                             │
├─────────────────────┬───────────────────────────────────────────────────┤
│                     │                                                   │
│   React Dashboard   │              FastAPI Backend                      │
│   (Vite + CSS)      │              (Python 3.x)                         │
│                     │                                                   │
│  ┌───────────────┐  │  ┌──────────────────────────────────────────────┐ │
│  │ Fraud Detector│◄─┼──┤ ML Engine (scikit-learn Random Forest)      │ │
│  │ Dashboard     │  │  │  ├─ 2000 synthetic transactions             │ │
│  ├───────────────┤  │  │  ├─ 80/20 train/test split                  │ │
│  │ ML Metrics    │◄─┼──┤  └─ XAI audit trail per prediction         │ │
│  │ Dashboard     │  │  ├──────────────────────────────────────────────┤ │
│  ├───────────────┤  │  │ Chargeback Responder (NLP Heuristic)        │ │
│  │ Chargeback    │◄─┼──┤  ├─ Claim classification engine             │ │
│  │ Dashboard     │  │  │  └─ Evidence letter generator               │ │
│  ├───────────────┤  │  ├──────────────────────────────────────────────┤ │
│  │ Abuse-Ring    │◄─┼──┤ Abuse-Ring Sentinel                         │ │
│  │ Dashboard     │  │  │  └─ IP/Device/Address graph clustering      │ │
│  ├───────────────┤  │  ├──────────────────────────────────────────────┤ │
│  │ Return-Risk   │◄─┼──┤ Return-Risk Scorer                          │ │
│  │ Dashboard     │  │  │  └─ Wardrobing fraud probability model      │ │
│  ├───────────────┤  │  ├──────────────────────────────────────────────┤ │
│  │ Underwriting  │◄─┼──┤ Underwriting Engine (NLP + Scraping)        │ │
│  │ Dashboard     │  │  │  ├─ BeautifulSoup4 web scraper              │ │
│  │               │  │  │  ├─ VADER sentiment analysis                │ │
│  │               │  │  │  └─ Word-boundary keyword detection         │ │
│  ├───────────────┤  │  ├──────────────────────────────────────────────┤ │
│  │ FX Risk       │◄─┼──┤ FX & Liquidity Risk Engine                  │ │
│  │ Dashboard     │  │  │  ├─ Frankfurter API (live FX rates)         │ │
│  │               │  │  │  ├─ RSS news feed ingestion                 │ │
│  │               │  │  │  └─ Sentiment-weighted risk scoring         │ │
│  └───────────────┘  │  └──────────────────────────────────────────────┘ │
│                     │                                                   │
│  Live Threat Ticker │  Activity Feed Generator                          │
│  (Real-time events) │  (Simulated threat stream)                        │
└─────────────────────┴───────────────────────────────────────────────────┘
```

## 🧩 The 6 Defense Modules

1. **Live Fraud-Spike Detector (ML)**
   - Evaluates live transactions against a Random Forest model using velocity, IP matching, and timing signals. Provides an Explainable AI (XAI) audit trail for every block.

2. **Chargeback Evidence Auto-Responder (NLP)**
   - Defeats "friendly fraud." Ingests customer dispute claims, cross-references internal logistics/cryptographic logs, and auto-generates formal Visa/Mastercard defense letters.

3. **Abuse-Ring Sentinel**
   - Daemon that scans transaction graphs for organized attacks (e.g., multiple unique cards tested against the same IP address or device fingerprint).

4. **Return-Risk Scorer (Wardrobing Fraud)**
   - Calculates the probability of a high-value return based on historical purchase/return ratios and dynamic cart values. Dynamically triggers restocking fees for high-risk carts.

5. **AI Merchant Underwriting (Compliance)**
   - Scrapes merchant websites on onboarding and runs NLP sentiment analysis + word-boundary-aware keyword detection to automatically flag prohibited businesses (crypto, adult, etc.).

6. **Macroeconomic FX & Liquidity Risk**
   - Ingests live global exchange rates (via Frankfurter API) and applies NLP sentiment analysis to live financial RSS feeds to predict global market volatility and settlement risk in real-time.

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Project info and available routes |
| `GET` | `/api/health` | Health check for operational verification |
| `POST` | `/api/fraud/predict` | Run ML fraud prediction on a transaction |
| `GET` | `/api/fraud/metrics` | Get model evaluation metrics (held-out test set) |
| `POST` | `/api/fraud/chargeback` | Generate chargeback defense evidence letter |
| `GET` | `/api/fraud/abuse-ring` | Get detected abuse-ring clusters |
| `POST` | `/api/fraud/return-risk` | Score return risk for a customer profile |
| `POST` | `/api/underwrite` | Run AI compliance analysis on a merchant URL |
| `GET` | `/api/fx-risk` | Get live FX rates + macro risk assessment |
| `GET` | `/api/fraud/activity-feed` | Get live activity events for threat ticker |

## 🛠️ Tech Stack & Architecture

*   **Backend:** Python, FastAPI, Uvicorn, scikit-learn (ML), BeautifulSoup4 (Scraping), VADER Sentiment (NLP).
*   **Frontend:** React, Vite, Vanilla CSS (Premium Cyber-Minimalist Dark Mode).
*   **Design:** Custom glassmorphism, responsive data visualization, and a real-time live threat ticker connected to the backend activity feed.

## ⚙️ How to Run the Project Locally

This is a monorepo containing both the backend AI engine and the frontend React dashboard. You will need two terminal windows to run both servers simultaneously.

### 1. Start the AI Backend Server
Open your first terminal and navigate to the `backend` folder:
```bash
cd backend
python -m venv venv
# On Windows use: .\venv\Scripts\activate
# On Mac/Linux use: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*The backend will now be running on `http://localhost:8000`*

### 2. Start the Frontend Dashboard
Open your second terminal and navigate to the `frontend` folder:
```bash
cd frontend
npm install
npm run dev
```
*The frontend will now be running on `http://localhost:5173`*

## 🔥 Post-Mortem: What Broke at 2 AM

During development, the **AI Merchant Underwriting** module began failing silently. The VADER sentiment analysis was returning bizarrely negative trust scores (like -80) for perfectly legitimate merchants.

**The Debugging Process:**
1. I logged the raw text being fed into the VADER analyzer.
2. I realized the `requests.get()` call was returning the raw HTML, and my initial `BeautifulSoup` parsing was extracting *all* text — including inline JavaScript, CSS styles, and minified code. 
3. The NLP model was trying to analyze code syntax like `function(e,t){return...}` and interpreting the dense, non-human syntax as highly negative sentiment.

**The Fix:**
I updated the scraper to explicitly extract and strip `<script>` and `<style>` tags before pulling the text (see `underwriting_engine.py` line 80). I also added a fallback: if the site blocks the scraper (which happens often with modern WAFs), the system gracefully degrades by injecting the URL itself into the text corpus so URL-based violations (e.g., `binance.com`) are still caught.

## 🛡️ Graceful Degradation & System Failures

A core requirement for the AI Risk Manager is handling system failures safely. The Vanguard Risk Engine implements fallback mechanisms across all external dependencies:

1. **FX API Outage:** If the live Frankfurter API goes down (or rate-limits us), the `fx_risk_engine` catches the `requests.exceptions.RequestException` and automatically falls back to a hardcoded set of baseline exchange rates. It continues to function, allowing the risk score to rely more heavily on the RSS news sentiment.
2. **Scraper Blocks (WAFs):** If a merchant's Cloudflare or WAF blocks our scraping bot (HTTP 403), the underwriting engine doesn't crash. It catches the error, alerts the system, and relies purely on URL pattern matching.
3. **Frontend API Failure:** If the backend goes offline, the frontend's Activity Feed falls back to a set of static, realistic events so the dashboard UI doesn't break, while showing a disconnected state.

## 🧪 Testing Guide

### Automated Tests (Backend)
```bash
cd backend
python -m pytest test_all.py -v
```

This runs the comprehensive test suite covering:
- ML model training, prediction, and metrics validation
- Underwriting keyword detection (including false-positive whitelist)
- FX risk engine data structure and bounds validation
- Edge cases (zero values, extreme amounts, missing schemes)

### Manual Testing (Full Stack)

1. Open `http://localhost:5173` in your browser.
2. Watch the **Live Stream Ticker** at the top right to see simulated real-time events generated by the backend.
3. In the **Fraud Detector**, submit a transaction with high velocity (e.g., >3) and an IP mismatch (No) to trigger the ML block.
4. In **ML Metrics**, observe the strict evaluation on the held-out test set, including F1 score and the False-Positive cost breakdown.
5. In **Chargeback Responder**, type a claim like "I never received this item" vs "This transaction is unauthorized" to see the NLP engine dynamically adjust the defense strategy.
6. In **Merchant Underwriting**, try a safe URL (`https://www.apple.com`) vs a prohibited one (`https://www.binance.com`) to see the compliance NLP in action.
7. Wait 30 seconds on the **FX Risk Engine** tab to watch it automatically poll live market rates and recalculate the global risk score.

---
*Built during the night shift for the Razorpay AI Buildathon.*
