import requests
import re
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# High-risk keywords for a payment gateway (simulating prohibited businesses)
PROHIBITED_KEYWORDS = [
    "crypto", "bitcoin", "ethereum", "tether", "binance", "coinbase", "kraken", "bybit", "kucoin",
    "casino", "gambling", "betting", "poker", "slots", "stake", "roulette", "sportsbook", "bet365",
    "weapons", "firearms", "ammunition", "gun", "rifle",
    "escort", "porn", "xxx", "counterfeit", "fake id", "dark web", "darknet",
    "weed", "cannabis", "marijuana", "narcotic"
]

HIGH_RISK_KEYWORDS = [
    "guaranteed returns", "investment scheme", "binary options", "trading bot",
    "lottery", "get rich quick", "multi-level marketing", "mlm", "pyramid scheme",
    "drop shipping", "dropshipping", "penny stock"
]

# Legitimate words that contain prohibited substrings — exclude these
FALSE_POSITIVE_WHITELIST = {
    "drugstore", "adult education", "adult learning", "adulting",
    "gundam", "burgundy", "gun control", "shotgun wedding",
    "stakehold", "stakeholder", "sweepstakes",
    "escort service"  # Keep this flagged
}


def _keyword_in_text(keyword: str, text: str) -> bool:
    """
    Check if a keyword exists in text using word-boundary-aware matching.
    Handles both multi-word phrases and single words.
    For URL components (containing dots), use simple substring matching.
    """
    # For URL-style patterns (e.g., "binance" in "binance.com"), use substring
    # Split text into URL portions and regular text portions
    # Simple approach: use regex word boundaries but also check for dot-separated tokens
    
    # First check with word boundaries (handles most cases correctly)
    pattern = r'(?:^|[\s\-_/\.])' + re.escape(keyword) + r'(?:$|[\s\-_/\.,;:!?\)])'
    if re.search(pattern, text, re.IGNORECASE):
        return True
    
    # Also check if keyword appears as part of URL/domain
    if '.' in text:
        # Check URL-like segments
        url_segments = re.findall(r'[\w\-]+(?:\.[\w\-]+)+', text)
        for segment in url_segments:
            parts = segment.lower().split('.')
            if keyword.lower() in parts:
                return True
    
    return False


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
        scrape_status = f"Successfully scraped {len(text)} characters from live website."

    except requests.exceptions.Timeout:
        scrape_status = "Connection timed out. Falling back to URL analysis."
    except requests.exceptions.ConnectionError:
        scrape_status = "Site unreachable. Falling back to URL analysis."
    except requests.exceptions.HTTPError as e:
        scrape_status = f"HTTP Error {e.response.status_code}. Falling back to URL analysis."
    except Exception as e:
        scrape_status = f"Site blocked scraper ({type(e).__name__}). Falling back to URL analysis."
        
    # If the site blocked us (or requires JS to load) and returned insufficient text
    if len(text) < 500:
        if "Successfully" in scrape_status:
            scrape_status = "Site requires JavaScript or returned minimal content. Relying heavily on URL analysis."

    # ALWAYS inject the URL itself into the text corpus so we never miss URL-based violations
    text = text + " " + url.lower()

    # Analyze Sentiment (only if we got meaningful text)
    if len(text) > 200:
        sentiment_scores = analyzer.polarity_scores(text)
    else:
        sentiment_scores = {'compound': 0.0}
    
    # Keyword Risk Analysis (word-boundary-aware matching)
    found_prohibited = []
    for kw in PROHIBITED_KEYWORDS:
        if _keyword_in_text(kw, text) and kw not in found_prohibited:
            found_prohibited.append(kw)

    found_high_risk = []
    for kw in HIGH_RISK_KEYWORDS:
        if _keyword_in_text(kw, text) and kw not in found_high_risk:
            found_high_risk.append(kw)
    
    # Calculate Trust Score (0-100) with weighted deductions
    trust_score = 100
    
    # Deductions
    if found_prohibited:
        # Scale by number of prohibited keywords found
        trust_score -= min(80, len(found_prohibited) * 25)
    if found_high_risk:
        trust_score -= min(30, len(found_high_risk) * 15)
        
    # If the site is extremely negative
    if sentiment_scores['compound'] < -0.5:
        trust_score -= 20
    elif sentiment_scores['compound'] < -0.2:
        trust_score -= 10
        
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
