from config import SEARCH_CRITERIA
from models import ProductCandidate
from scoring import score_candidate


def test_search_criteria_has_us_to_de_target_values():
    assert SEARCH_CRITERIA["market"] == "US_TO_DE"
    assert SEARCH_CRITERIA["min_roi_percent"] > 0
    assert SEARCH_CRITERIA["max_risk_level"] == "medium"


def test_candidate_scoring_rewards_profitable_and_low_risk_products():
    candidate = ProductCandidate(
        product_name="Portable Blender",
        asin="B0TEST001",
        us_price=19.99,
        de_price=52.99,
        monthly_sales=1800,
        fba_sellers=4,
        amazon_seller=False,
        estimated_profit=12.00,
        estimated_roi=58.0,
        risk_level="low",
        category="Kitchen",
        image_url="https://example.com/img.png",
    )

    score = score_candidate(candidate, SEARCH_CRITERIA)

    assert 70 <= score <= 100


def test_candidate_scoring_penalizes_high_risk_products():
    candidate = ProductCandidate(
        product_name="Unsafe Item",
        asin="B0TEST002",
        us_price=35.0,
        de_price=90.0,
        monthly_sales=110,
        fba_sellers=18,
        amazon_seller=True,
        estimated_profit=2.0,
        estimated_roi=8.0,
        risk_level="high",
        category="Hazmat",
        image_url="https://example.com/bad.png",
    )

    score = score_candidate(candidate, SEARCH_CRITERIA)

    assert score < 50
