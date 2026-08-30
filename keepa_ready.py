from pathlib import Path


def build_keepa_payload(candidate: dict) -> dict:
    payload = {
        "asin": candidate.get("asin"),
        "product_name": candidate.get("product_name") or candidate.get("verified_title"),
        "verified_title": candidate.get("verified_title") or candidate.get("product_name"),
        "us_price": candidate.get("us_price"),
        "de_price": candidate.get("de_price"),
        "verified_price": candidate.get("verified_price") or candidate.get("de_price"),
        "roi": candidate.get("roi"),
        "score": candidate.get("score"),
        "market": candidate.get("market") or "US_TO_DE",
        "status": "keepa_ready",
        "is_valid_amazon_product": candidate.get("is_valid_amazon_product", False),
        "source_url": candidate.get("url") or candidate.get("source_url"),
        "image_url": candidate.get("verified_image_url") or candidate.get("image_url"),
    }
    return payload


def build_keepa_api_request(candidates, api_key: str = "", market: str = "com") -> dict:
    payload = [build_keepa_payload(item) for item in candidates]
    return {
        "api_key": api_key,
        "market": market,
        "asins": [item.get("asin") for item in payload if item.get("asin")],
        "items": payload,
    }


def save_keepa_queue(candidates, output_path: str = "data/keepa_ready.json"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [build_keepa_payload(item) for item in candidates]
    path.write_text(str(payload), encoding="utf-8")
    return str(path)
