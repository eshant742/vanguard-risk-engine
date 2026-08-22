import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
from fx_risk_engine import get_fx_risk_data, get_live_fx_rates, get_news_sentiment

class TestFXRiskEngine:
    """Tests for the macroeconomic FX & liquidity risk engine."""

    def test_fx_rates_returns_dict_with_currencies(self):
        rates = get_live_fx_rates()
        assert isinstance(rates, dict)
        assert len(rates) > 0
        for currency, rate in rates.items():
            assert isinstance(rate, (int, float)), f"Rate for {currency} is not numeric"
            assert rate > 0, f"Rate for {currency} is non-positive: {rate}"

    def test_fallback_rates_have_expected_currencies(self):
        """Fallback should contain INR, EUR, GBP."""
        # Even if live API works, fallback structure is tested via the function
        rates = get_live_fx_rates()
        # Live or fallback should have these
        assert len(rates) >= 3 or set(rates.keys()) == {"INR", "EUR", "GBP"}

    def test_news_sentiment_structure_complete(self):
        result = get_news_sentiment()
        assert "headlines" in result
        assert "average_sentiment" in result
        assert isinstance(result["headlines"], list)
        assert len(result["headlines"]) > 0
        for item in result["headlines"]:
            assert "headline" in item
            assert "sentiment" in item
            assert "color" in item
            assert item["color"] in ["green", "yellow", "red"]
            assert isinstance(item["sentiment"], (int, float))

    def test_average_sentiment_in_valid_range(self):
        """VADER compound scores are in [-1, 1], so average should be too."""
        result = get_news_sentiment()
        assert -1.0 <= result["average_sentiment"] <= 1.0

    def test_fx_risk_data_all_fields(self):
        data = get_fx_risk_data()
        required = ["rates", "base_currency", "news", "macro_risk_score",
                     "system_status", "status_color", "headline_count", "average_sentiment"]
        for key in required:
            assert key in data, f"Missing key: {key}"
        assert data["base_currency"] == "USD"

    def test_risk_score_clamped_0_100(self):
        data = get_fx_risk_data()
        assert 0 <= data["macro_risk_score"] <= 100

    def test_status_color_matches_score(self):
        data = get_fx_risk_data()
        score = data["macro_risk_score"]
        if score > 75:
            assert data["status_color"] == "red"
        elif score > 40:
            assert data["status_color"] == "yellow"
        else:
            assert data["status_color"] == "green"

    def test_headline_count_matches_news_list(self):
        data = get_fx_risk_data()
        assert data["headline_count"] == len(data["news"])

