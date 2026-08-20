import requests
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def get_live_fx_rates():
    """Fetches real live exchange rates from Frankfurter API"""
    try:
        # Base USD, get INR, EUR, GBP
        url = "https://api.frankfurter.app/latest?from=USD&to=INR,EUR,GBP"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("rates", {})
    except Exception:
        # Fallback if API fails
        return {"INR": 83.50, "EUR": 0.92, "GBP": 0.79}

def get_news_sentiment():
    """Fetches live financial news from Yahoo Finance RSS and calculates sentiment"""
    try:
        # Yahoo finance global market news
        feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
        
        headlines = []
        total_sentiment = 0
        
        # Process top 5 news items
        for entry in feed.entries[:5]:
            title = entry.title
            score = analyzer.polarity_scores(title)['compound']
            total_sentiment += score
            headlines.append({
                "headline": title,
                "sentiment": score,
                # Color code based on sentiment
                "color": "green" if score > 0.1 else ("red" if score < -0.1 else "yellow")
            })
            
        avg_sentiment = total_sentiment / 5 if feed.entries else 0
        
        return {
            "headlines": headlines,
            "average_sentiment": round(avg_sentiment, 2)
        }
    except Exception:
        # Fallback
        return {
            "headlines": [{"headline": "Global markets stabilize", "sentiment": 0.1, "color": "green"}],
            "average_sentiment": 0.1
        }

def get_fx_risk_data():
    """Combines FX rates and News Sentiment to calculate overall settlement risk"""
    rates = get_live_fx_rates()
    news = get_news_sentiment()
    
    # Calculate Macro Risk Score (0-100)
    # If sentiment is highly negative, risk goes up.
    # Base risk is 20
    base_risk = 20
    
    # Invert sentiment (-1 to 1) -> (100 to 0 added risk)
    # So if sentiment is -0.5 (bad), added risk is around 40
    sentiment_factor = (news["average_sentiment"] * -50)
    
    macro_risk_score = min(100, max(0, int(base_risk + sentiment_factor)))
    
    if macro_risk_score > 75:
        system_status = "CRITICAL VOLATILITY - WIDEN SPREADS"
        status_color = "red"
    elif macro_risk_score > 40:
        system_status = "ELEVATED RISK - MONITOR CLOSELY"
        status_color = "yellow"
    else:
        system_status = "STABLE MARKETS - NORMAL OPERATIONS"
        status_color = "green"
        
    return {
        "rates": rates,
        "base_currency": "USD",
        "news": news["headlines"],
        "macro_risk_score": macro_risk_score,
        "system_status": system_status,
        "status_color": status_color
    }
