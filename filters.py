from config import SEARCH_CRITERIA


def passes_criteria(candidate, criteria=None) -> bool:
    if criteria is None:
        criteria = SEARCH_CRITERIA

    if candidate.monthly_sales < criteria.get("min_monthly_sales", 0):
        return False
    if candidate.estimated_roi < criteria.get("min_roi_percent", 0):
        return False
    if candidate.fba_sellers > criteria.get("max_fba_sellers", 999):
        return False
    if candidate.risk_level.lower() not in {"low", "medium"}:
        if criteria.get("max_risk_level") in {"low", "medium"}:
            return False
    if criteria.get("exclude_hazmat") and candidate.category.lower() == "hazmat":
        return False
    if criteria.get("prefer_no_amazon_seller") and candidate.amazon_seller:
        return False
    if candidate.category not in criteria.get("product_categories", []):
        return False

    return True


def filter_candidates(candidates, criteria=None):
    if criteria is None:
        criteria = SEARCH_CRITERIA
    return [candidate for candidate in candidates if passes_criteria(candidate, criteria)]
