from ai_assessor import generate_ai_summary
from config import SEARCH_CRITERIA
from data_sources import build_real_source_plan
from filters import filter_candidates
from scoring import score_candidate
from search_provider import fetch_search_results


def build_research_report(candidates, criteria=None):
    if criteria is None:
        criteria = SEARCH_CRITERIA

    valid = filter_candidates(candidates, criteria)
    ranked = []

    for candidate in valid:
        score = score_candidate(candidate, criteria)
        summary = generate_ai_summary(candidate, criteria)
        status = "Strong candidate" if score >= 75 else "Watchlist" if score >= 50 else "Low priority"
        ranked.append(
            {
                "product_name": candidate.product_name,
                "asin": candidate.asin,
                "us_price": candidate.us_price,
                "de_price": candidate.de_price,
                "monthly_sales": candidate.monthly_sales,
                "fba_sellers": candidate.fba_sellers,
                "amazon_seller": candidate.amazon_seller,
                "profit": candidate.estimated_profit,
                "roi": candidate.estimated_roi,
                "risk_level": candidate.risk_level,
                "score": round(score, 1),
                "status": status,
                "ai_summary": summary,
            }
        )

    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def run_research_scan(search_terms=None, market="com", criteria=None):
    if search_terms is None:
        search_terms = ["portable blender", "desk organizer", "water bottle"]

    if criteria is None:
        criteria = SEARCH_CRITERIA

    search_results = []
    for keyword in search_terms:
        result = fetch_search_results(keyword, market=market)
        source_plan = build_real_source_plan(keyword, market=market)
        search_results.extend(
            [{
                "keyword": keyword,
                "asin": item["asin"],
                "title": item["title"],
                "url": result["url"],
                "source": result.get("source", "unknown"),
                "source_plan": source_plan,
                "roi": item.get("roi", 0),
                "monthly_sales": item.get("monthly_sales", 0),
            } for item in result["results"]]
        )

    return {
        "criteria": criteria,
        "search_terms": search_terms,
        "search_results": search_results,
        "ranked_candidates": [],
    }
