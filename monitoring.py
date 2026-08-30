def compare_candidates_with_history(current_candidates, history_records):
    history_map = {item.get("asin"): item for item in history_records if item.get("asin")}
    changes = []

    for item in current_candidates:
        asin = item.get("asin")
        prev = history_map.get(asin)
        if prev is None:
            continue

        de_price_change = float(item.get("de_price", 0) or 0) - float(prev.get("de_price", 0) or 0)
        roi_change = float(item.get("roi", 0) or 0) - float(prev.get("roi", 0) or 0)
        score_change = float(item.get("score", 0) or 0) - float(prev.get("score", 0) or 0)

        if de_price_change != 0 or roi_change != 0 or score_change != 0:
            changes.append({
                "asin": asin,
                "product_name": item.get("product_name"),
                "de_price_change": round(de_price_change, 2),
                "roi_change": round(roi_change, 2),
                "score_change": round(score_change, 2),
            })

    return changes
