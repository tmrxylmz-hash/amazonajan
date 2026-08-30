from product_matcher import (
    build_amazon_de_search_url,
    compare_market_pair,
    calculate_competition_score,
)


def test_build_amazon_de_search_url_uses_asin_keyword():
    url = build_amazon_de_search_url("B0TEST123")
    assert "amazon.de/s" in url
    assert "B0TEST123" in url


def test_compare_market_pair_estimates_de_price_and_roi():
    result = compare_market_pair(us_price=19.99)
    assert result["de_price"] > result["us_price"]
    assert result["roi_percent"] > 0
    assert result["target_market"] == "DE"


def test_calculate_competition_score_penalizes_amazon_seller_and_many_fba_sellers():
    score = calculate_competition_score(fba_sellers=16, amazon_seller=True)
    assert 0 <= score <= 100
    assert score < 60
