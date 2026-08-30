from config import SEARCH_CRITERIA
from filters import filter_candidates, passes_criteria
from models import ProductCandidate


def test_passes_criteria_for_valid_candidate():
    candidate = ProductCandidate(
        product_name="Valid Product",
        asin="B0OK001",
        us_price=15.0,
        de_price=42.0,
        monthly_sales=1200,
        fba_sellers=5,
        amazon_seller=False,
        estimated_profit=9.5,
        estimated_roi=35.0,
        risk_level="low",
        category="Kitchen",
    )

    assert passes_criteria(candidate, SEARCH_CRITERIA) is True


def test_filter_candidates_excludes_weak_matches():
    candidates = [
        ProductCandidate(
            product_name="Good",
            asin="B0GOOD",
            us_price=16.0,
            de_price=43.0,
            monthly_sales=2000,
            fba_sellers=3,
            amazon_seller=False,
            estimated_profit=11.0,
            estimated_roi=50.0,
            risk_level="low",
            category="Kitchen",
        ),
        ProductCandidate(
            product_name="Reject",
            asin="B0BAD",
            us_price=30.0,
            de_price=70.0,
            monthly_sales=100,
            fba_sellers=20,
            amazon_seller=True,
            estimated_profit=1.0,
            estimated_roi=6.0,
            risk_level="high",
            category="Hazmat",
        ),
    ]

    filtered = filter_candidates(candidates, SEARCH_CRITERIA)

    assert len(filtered) == 1
    assert filtered[0].asin == "B0GOOD"
