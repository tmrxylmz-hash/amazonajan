from config import SEARCH_CRITERIA


RISK_WEIGHTS = {
    "low": 1.0,
    "medium": 0.7,
    "high": 0.35,
}


def _score_profitability(candidate) -> float:
    roi = max(candidate.estimated_roi, 0)
    return min(40.0, roi * 0.55)


def _score_sales(candidate) -> float:
    if candidate.monthly_sales <= 0:
        return 0.0
    return min(25.0, candidate.monthly_sales / 80.0)


def _score_competition(candidate) -> float:
    # Lower competitive pressure is better.
    if candidate.fba_sellers <= 0:
        return 15.0
    return max(0.0, 15.0 - (candidate.fba_sellers * 1.2))


def _score_risk(candidate) -> float:
    weight = RISK_WEIGHTS.get(candidate.risk_level.lower(), 0.5)
    return max(0.0, 20.0 * weight)


def _score_market_fit(candidate) -> float:
    # Prefer non-Amazon sellers and good Germany price position.
    fit = 0.0
    if candidate.de_price > candidate.us_price:
        fit += 8.0
    if not candidate.amazon_seller:
        fit += 7.0
    if candidate.category in SEARCH_CRITERIA.get("product_categories", []):
        fit += 5.0
    return min(20.0, fit)


def score_candidate(candidate, criteria=None) -> float:
    if criteria is None:
        criteria = SEARCH_CRITERIA

    score = 0.0
    score += _score_profitability(candidate)
    score += _score_sales(candidate)
    score += _score_competition(candidate)
    score += _score_risk(candidate)
    score += _score_market_fit(candidate)

    if candidate.amazon_seller and criteria.get("prefer_no_amazon_seller"):
        score -= 15.0
    if candidate.risk_level.lower() == "high":
        score -= 10.0
    if candidate.estimated_profit <= 0:
        score -= 20.0

    return max(0.0, min(100.0, score))
