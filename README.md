# Vanguard Risk Engine

**Razorpay AI Builder Internship 2026 - AI Risk Manager Track**

Vanguard is a unified, autonomous Risk Management platform designed to tackle the two most critical phases of a payment gateway's lifecycle:
1. **Micro-Risk (Merchant Onboarding):** An AI agent that autonomously scrapes merchant websites, evaluates compliance against acceptable-use policies, and uses NLP sentiment analysis to generate instant Trust Scores.
2. **Macro-Risk (Liquidity & FX):** A real-time engine that ingests live global exchange rates (via Frankfurter API) and applies VADER NLP sentiment analysis to live financial RSS feeds to predict global market volatility and settlement risk.

## 🚀 Tech Stack
*   **Backend:** Python, FastAPI, Uvicorn, BeautifulSoup4, VADER Sentiment NLP
*   **Frontend:** React, Vite, Vanilla CSS (Premium Dark Mode & Glassmorphism)

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

## 🧪 Testing the AI

1. Open `http://localhost:5173` in your browser.
2. Navigate to the **Merchant Underwriting** tab.
3. Try entering a safe website (e.g., `https://www.apple.com`) to see a 100 Trust Score.
4. Try entering a prohibited website (e.g., `https://www.binance.com`) to watch the AI catch the crypto keywords and automatically issue a REJECT action.
5. Navigate to the **FX & Liquidity Risk** tab to watch the AI stream live global exchange rates and analyze live news sentiment in real-time.
