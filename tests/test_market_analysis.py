from market_analysis import analyze_candidate, calculate_profit, estimate_de_price


def test_estimate_de_price_uses_reasonable_euro_multiplier():
    de_price = estimate_de_price(20.0)
    assert 40 < de_price < 60


def test_analyze_candidate_returns_profit_and_roi_for_us_to_de_flow():
    candidate = analyze_candidate({
        "title": "Portable Blender",
        "us_price": 19.99,
        "monthly_sales": 1200,
    })

    assert candidate["title"] == "Portable Blender"
    assert candidate["de_price"] > candidate["us_price"]
    assert candidate["roi_percent"] > 0
    assert candidate["estimated_profit"] > 0


def test_calculate_profit_uses_basic_fee_model():
    profit = calculate_profit(20.0, 52.0)
    assert profit > 0
