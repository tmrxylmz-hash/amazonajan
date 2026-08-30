from urllib.parse import quote_plus


def build_amazon_de_search_url(asin_or_keyword: str) -> str:
    return f"https://www.amazon.de/s?k={quote_plus(asin_or_keyword)}"


def compare_market_pair(us_price: float, us_cost: float = 0.0, eur_multiplier: float = 2.4) -> dict:
    if us_price <= 0:
        return {"target_market": "DE", "us_price": 0.0, "de_price": 0.0, "roi_percent": 0.0}

    de_price = round(us_price * eur_multiplier, 2)
    if us_cost <= 0:
        us_cost = us_price * 0.55
    referral_fee = de_price * 0.15
    fba_fee = 4.0
    estimated_profit = round(de_price - us_cost - referral_fee - fba_fee, 2)
    roi_percent = round((estimated_profit / us_cost) * 100, 2) if us_cost > 0 else 0.0

    return {
        "target_market": "DE",
        "us_price": round(us_price, 2),
        "de_price": round(de_price, 2),
        "estimated_profit": estimated_profit,
        "roi_percent": roi_percent,
    }


def calculate_competition_score(fba_sellers: int = 0, amazon_seller: bool = False) -> float:
    score = 100.0
    score -= min(fba_sellers * 4, 50)
    if amazon_seller:
        score -= 25
    return max(0.0, round(score, 2))
