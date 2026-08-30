def estimate_de_price(us_price: float, eur_multiplier: float = 2.4) -> float:
    if us_price <= 0:
        return 0.0
    return round(us_price * eur_multiplier, 2)


def calculate_profit(us_cost: float, de_price: float, referral_fee_rate: float = 0.15, fba_fee: float = 4.0) -> float:
    if us_cost <= 0 or de_price <= 0:
        return 0.0
    referral_fee = de_price * referral_fee_rate
    return round(de_price - us_cost - referral_fee - fba_fee, 2)


def analyze_candidate(candidate: dict) -> dict:
    title = candidate.get("title", "Unknown")
    us_price = float(candidate.get("us_price", 0.0) or 0.0)
    monthly_sales = int(candidate.get("monthly_sales", 0) or 0)

    de_price = estimate_de_price(us_price)
    profit = calculate_profit(us_price, de_price)
    roi_percent = 0.0
    if us_price > 0:
        roi_percent = round((profit / us_price) * 100, 2)

    return {
        "title": title,
        "us_price": round(us_price, 2),
        "de_price": round(de_price, 2),
        "monthly_sales": monthly_sales,
        "estimated_profit": profit,
        "roi_percent": roi_percent,
    }
