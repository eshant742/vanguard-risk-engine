import logging
import requests
import re
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger("vanguard.underwriting")
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

# Legitimate words that contain prohibited substrings — exclude these from flagging
FALSE_POSITIVE_WHITELIST = {
    "drugstore", "adult education", "adult learning", "adulting",
    "gundam", "burgundy", "gun control", "shotgun wedding",
    "stakehold", "stakeholder", "sweepstakes",
}


def _context_is_whitelisted(keyword: str, text: str) -> bool:
    """
    Check if a keyword match is actually part of a whitelisted phrase.
    Returns True if the match should be suppressed (false positive).
    """
    text_lower = text.lower()
    for whitelisted_phrase in FALSE_POSITIVE_WHITELIST:
        if keyword in whitelisted_phrase and whitelisted_phrase in text_lower:
            return True
    return False


def _keyword_in_text(keyword: str, text: str) -> bool:
    """
    Check if a keyword exists in text using word-boundary-aware matching.
    Handles both multi-word phrases and single words, including URL segments.
    """
    # \b matches word boundaries, perfectly handling spaces, dots, slashes, etc.
    # This prevents 'gun' from matching 'burgundy' but allows it to match 'example.com/gun'
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


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
    
    # Keyword Risk Analysis (word-boundary-aware matching with whitelist filtering)
    found_prohibited = []
    for kw in PROHIBITED_KEYWORDS:
        if _keyword_in_text(kw, text) and kw not in found_prohibited:
            if not _context_is_whitelisted(kw, text):
                found_prohibited.append(kw)

    found_high_risk = []
    for kw in HIGH_RISK_KEYWORDS:
        if _keyword_in_text(kw, text) and kw not in found_high_risk:
            if not _context_is_whitelisted(kw, text):
                found_high_risk.append(kw)
    
    # Calculate Trust Score (0-100) with weighted deductions
    trust_score = 100
    
    # Deductions
    if found_prohibited:
        # Prohibited items are severe violations. Any single violation drops score below REJECT threshold.
        trust_score -= 75 + (len(found_prohibited) * 10)
    if found_high_risk:
        # High risk items are a warning
        trust_score -= min(40, len(found_high_risk) * 20)
        
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
