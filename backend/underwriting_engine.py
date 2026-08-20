import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

analyzer = SentimentIntensityAnalyzer()

# High-risk keywords for a payment gateway (simulating prohibited businesses)
PROHIBITED_KEYWORDS = [
    "crypto", "bitcoin", "ethereum", "tether", "binance", "coinbase", "kraken", 
    "casino", "gambling", "betting", "poker", "slots",
    "weapons", "firearms", "ammunition",
    "escort", "adult", "porn", "counterfeit", "fake id", "dark web"
]

HIGH_RISK_KEYWORDS = [
    "guaranteed returns", "investment", "forex", "binary options", "trading bot",
    "lottery", "get rich quick", "multi-level marketing", "mlm", "amway", "herbalife",
    "drop shipping", "dropshipping"
]

def analyze_merchant(url: str):
    """
    Scrapes the merchant URL, analyzes text for compliance and sentiment.
    """
    # Ensure URL has scheme
    if not url.startswith("http"):
        url = "https://" + url

    text = ""
    scrape_status = ""

    try:
        # Simulate a real browser to avoid basic blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract visible text
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True).lower()
        scrape_status = f"Scraped {len(text)} characters."

    except Exception as e:
        scrape_status = f"Site blocked scraper (Error: {type(e).__name__}). Falling back to URL analysis."
        
    # If the site blocked us (or requires JS to load) and returned no text, fallback to the URL string
    if len(text) < 50:
        text = url.lower()
        if "blocked" not in scrape_status:
            scrape_status = "Site requires JavaScript or blocked scraper. Falling back to URL analysis."

    # Analyze Sentiment (only if we got real text, otherwise neutral)
    if len(text) > 200:
        sentiment_scores = analyzer.polarity_scores(text)
    else:
        sentiment_scores = {'compound': 0.0}
    
    # Keyword Risk Analysis
    found_prohibited = [kw for kw in PROHIBITED_KEYWORDS if re.search(r'\b' + kw + r'\b', text)]
    
    # Also check substring match just in case regex \b fails on URLs (e.g. binance.com -> binance)
    for kw in PROHIBITED_KEYWORDS:
        if kw in text and kw not in found_prohibited:
            found_prohibited.append(kw)

    found_high_risk = [kw for kw in HIGH_RISK_KEYWORDS if re.search(r'\b' + kw + r'\b', text)]
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text and kw not in found_high_risk:
            found_high_risk.append(kw)
    
    # Calculate Trust Score (0-100)
    trust_score = 100
    
    # Deductions
    if found_prohibited:
        trust_score -= 80  # Immediate massive flag
    if found_high_risk:
        trust_score -= 30
        
    # If the site is extremely negative
    if sentiment_scores['compound'] < -0.2:
        trust_score -= 15
        
    # Ensure score is within bounds
    trust_score = max(0, min(100, trust_score))
    
    # Determine Status
    if trust_score < 40:
        status = "REJECT"
        action_color = "red"
    elif trust_score < 70:
        status = "MANUAL REVIEW"
        action_color = "yellow"
    else:
        status = "APPROVE"
        action_color = "green"

    return {
        "url": url,
        "trust_score": trust_score,
        "status": status,
        "action_color": action_color,
        "flags": {
            "prohibited_items": list(set(found_prohibited)),
            "high_risk_items": list(set(found_high_risk)),
            "sentiment_compound": round(sentiment_scores['compound'], 2)
        },
        "summary": f"{scrape_status} Found {len(set(found_prohibited))} prohibited and {len(set(found_high_risk))} high-risk terms."
    }
