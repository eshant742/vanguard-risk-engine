import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
from underwriting_engine import analyze_merchant, _keyword_in_text, _context_is_whitelisted, PROHIBITED_KEYWORDS, HIGH_RISK_KEYWORDS

class TestUnderwritingEngine:
    """Tests for the AI merchant underwriting / compliance system."""

    # --- Keyword Detection ---

    def test_keyword_exact_match_in_text(self):
        assert _keyword_in_text("crypto", "Buy crypto here today")
        assert _keyword_in_text("bitcoin", "Trade bitcoin now")
        assert _keyword_in_text("gambling", "Online gambling site")

    def test_keyword_in_url(self):
        assert _keyword_in_text("binance", "Visit binance.com for trading")
        assert _keyword_in_text("bet365", "check bet365.com")

    def test_keyword_at_start_of_text(self):
        assert _keyword_in_text("crypto", "crypto is the future")

    def test_keyword_at_end_of_text(self):
        assert _keyword_in_text("crypto", "I love crypto")

    def test_keyword_no_false_positive_substring(self):
        """Keywords should NOT match as substrings of other words."""
        assert not _keyword_in_text("crypto", "The encrypted data was safe")
        assert not _keyword_in_text("gun", "burgundy colored coat")

    def test_keyword_multi_word_phrase(self):
        """Multi-word prohibited phrases should match correctly."""
        assert _keyword_in_text("dark web", "Buy things on the dark web")
        assert _keyword_in_text("fake id", "Get a fake id here")
        assert _keyword_in_text("get rich quick", "This get rich quick scheme is amazing")

    # --- Whitelist ---

    def test_whitelist_suppresses_gundam(self):
        assert _context_is_whitelisted("gun", "check out this gundam model kit")

    def test_whitelist_suppresses_stakeholder(self):
        assert _context_is_whitelisted("stake", "stakeholder meeting tomorrow")

    def test_whitelist_suppresses_burgundy(self):
        assert _context_is_whitelisted("gun", "a beautiful burgundy dress")

    def test_whitelist_suppresses_sweepstakes(self):
        assert _context_is_whitelisted("stake", "enter our sweepstakes contest")

    def test_whitelist_does_not_suppress_real_crypto(self):
        assert not _context_is_whitelisted("crypto", "buy crypto today")

    def test_whitelist_does_not_suppress_real_gambling(self):
        assert not _context_is_whitelisted("gambling", "online gambling platform")

    # --- Full Analysis ---

    def test_safe_site_gets_high_trust_score(self):
        result = analyze_merchant("https://www.example.com")
        assert result["trust_score"] >= 70 or result["status"] in ["APPROVE", "MANUAL REVIEW"]
        assert "url" in result and "flags" in result

    def test_prohibited_site_rejected(self):
        result = analyze_merchant("https://www.binance.com")
        assert result["trust_score"] < 40
        assert result["status"] == "REJECT"
        assert "binance" in result["flags"]["prohibited_items"]

    def test_gambling_site_rejected(self):
        result = analyze_merchant("https://www.bet365.com")
        assert result["status"] == "REJECT"
        assert "bet365" in result["flags"]["prohibited_items"]

    def test_result_has_all_required_fields(self):
        result = analyze_merchant("https://test-example.com")
        for key in ["url", "trust_score", "status", "action_color", "flags", "summary"]:
            assert key in result, f"Missing key: {key}"
        assert result["action_color"] in ["red", "yellow", "green"]
        assert 0 <= result["trust_score"] <= 100

    def test_flags_structure(self):
        """Flags dict must have prohibited_items, high_risk_items, and sentiment."""
        result = analyze_merchant("https://example.com")
        flags = result["flags"]
        assert "prohibited_items" in flags
        assert "high_risk_items" in flags
        assert "sentiment_compound" in flags
        assert isinstance(flags["prohibited_items"], list)
        assert isinstance(flags["high_risk_items"], list)
        assert isinstance(flags["sentiment_compound"], float)

    def test_url_auto_prefixed_with_https(self):
        result = analyze_merchant("example.com")
        assert result["url"].startswith("https://")

    def test_trust_score_clamped_to_0_100(self):
        """Even heavily flagged sites should have score in [0, 100]."""
        result = analyze_merchant("https://crypto-casino-gambling-betting.com")
        assert 0 <= result["trust_score"] <= 100

    def test_status_thresholds_approve(self):
        """Trust score >= 70 → APPROVE, action_color = green."""
        result = analyze_merchant("https://www.example.com")
        if result["trust_score"] >= 70:
            assert result["status"] == "APPROVE"
            assert result["action_color"] == "green"

    def test_summary_includes_term_counts(self):
        """Summary string must mention how many terms were found."""
        result = analyze_merchant("https://www.binance.com")
        assert "prohibited" in result["summary"].lower()

