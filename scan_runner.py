from product_matcher import compare_market_pair, calculate_competition_score
from research_engine import run_research_scan


def deduplicate_candidates(candidates):
    by_asin = {}
    for item in candidates:
        asin = item.get("asin") or item.get("product_name")
        current = by_asin.get(asin)
        if current is None or item.get("score", 0) > current.get("score", 0):
            by_asin[asin] = item
    return sorted(by_asin.values(), key=lambda x: x.get("score", 0), reverse=True)


def run_scan_cycle(search_terms, criteria=None, market="com"):
    raw = run_research_scan(search_terms, market=market, criteria=criteria)
    candidates = []
    filter_criteria = criteria or {}
    min_roi = float(filter_criteria.get("min_roi_percent", 0))
    min_sales = int(filter_criteria.get("min_monthly_sales", 0))

    for item in raw["search_results"]:
        us_price = 24.99
        market_data = compare_market_pair(us_price)
        competition = calculate_competition_score(fba_sellers=8, amazon_seller=False)
        candidate_roi = float(item.get("roi", market_data["roi_percent"]))
        candidate_sales = int(item.get("monthly_sales", 1200))
        candidate = {
            "product_name": item["title"],
            "asin": item["asin"],
            "us_price": us_price,
            "de_price": market_data["de_price"],
            "monthly_sales": candidate_sales,
            "roi": candidate_roi,
            "score": competition,
            "source": item.get("source", "search"),
            "market": market,
        }

        if candidate["roi"] < min_roi:
            continue
        if candidate["monthly_sales"] < min_sales:
            continue
        candidates.append(candidate)

    deduped = deduplicate_candidates(candidates)

    return {
        "search_terms": search_terms,
        "candidates": deduped,
        "candidate_count": len(deduped),
        "source": "scan_cycle",
    }
