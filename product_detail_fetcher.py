import re
from urllib.parse import quote_plus

from data_sources import build_request_session


def build_product_url(asin: str, market: str = "com") -> str:
    market_map = {
        "com": "https://www.amazon.com/dp/{asin}",
        "de": "https://www.amazon.de/dp/{asin}",
    }
    domain = market_map.get(market.lower(), market_map["com"])
    return domain.format(asin=quote_plus(asin))


def is_valid_amazon_product_page(html: str, asin: str) -> bool:
    if not html:
        return False
    if "amazon" not in html.lower() and "producttitle" not in html.lower() and "a-price-whole" not in html.lower():
        return False
    asin_markers = [
        f'data-asin="{asin}"',
        f'asin={asin}',
        asin,
    ]
    title_marker = re.search(r'<span[^>]*id=["\']productTitle["\'][^>]*>', html, re.IGNORECASE)
    price_marker = re.search(r'a-price-whole|a-price-fraction', html, re.IGNORECASE)
    if not title_marker or not price_marker:
        return False
    if not any(marker in html for marker in asin_markers):
        return False
    return True


def extract_detail_fields(html: str):
    title = ""
    image_url = ""
    price = 0.0

    title_match = re.search(r'<span[^>]*id=["\']productTitle["\'][^>]*>(.*?)</span>', html, re.DOTALL | re.IGNORECASE)
    if title_match:
        title = re.sub(r'<.*?>', '', title_match.group(1))
        title = ' '.join(title.split())

    image_match = re.search(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', html, re.DOTALL | re.IGNORECASE)
    if image_match:
        image_url = image_match.group(1)

    whole_match = re.search(r'<span[^>]*class=["\']a-price-whole["\'][^>]*>([0-9,]+)', html, re.DOTALL | re.IGNORECASE)
    fraction_match = re.search(r'<span[^>]*class=["\']a-price-fraction["\'][^>]*>([0-9]+)', html, re.DOTALL | re.IGNORECASE)

    if whole_match:
        whole = whole_match.group(1).replace(',', '')
        fraction = fraction_match.group(1) if fraction_match else '00'
        price = float(f"{whole}.{fraction}")

    return {
        "title": title,
        "price": round(price, 2),
        "image_url": image_url,
        "currency": "USD",
    }


def fetch_real_market_data_for_asin(asin: str, market: str = "com", request_session=None):
    url = build_product_url(asin, market)
    if request_session is None:
        request_session = build_request_session()

    response = request_session.get(url, timeout=20)
    response.raise_for_status()
    html = response.text
    valid = is_valid_amazon_product_page(html, asin)
    details = extract_detail_fields(html)

    return {
        "asin": asin,
        "market": market,
        "url": url,
        "is_valid_amazon_product": valid,
        "title": details.get("title", ""),
        "price": details.get("price", 0.0),
        "image_url": details.get("image_url", ""),
        "currency": details.get("currency", "USD"),
    }


def enrich_candidate_with_asin_detail(candidate: dict, market: str = "com", request_session=None):
    asin = candidate.get("asin")
    if not asin:
        return {**candidate, "is_valid_amazon_product": False}

    data = fetch_real_market_data_for_asin(asin, market=market, request_session=request_session)
    enriched = dict(candidate)
    enriched.update({
        "market": data["market"],
        "url": data["url"],
        "is_valid_amazon_product": data["is_valid_amazon_product"],
        "verified_title": data["title"] or candidate.get("product_name"),
        "verified_price": data["price"],
        "verified_image_url": data["image_url"],
        "currency": data["currency"],
    })
    if data["title"]:
        enriched["product_name"] = data["title"]
    return enriched


def fetch_product_details(asin: str, market: str = "com", request_session=None):
    data = fetch_real_market_data_for_asin(asin, market, request_session=request_session)
    if not data["is_valid_amazon_product"]:
        raise ValueError(f"ASIN {asin} did not resolve to a valid Amazon product page for market {market}")
    return {
        "asin": data["asin"],
        "title": data["title"],
        "price": data["price"],
        "image_url": data["image_url"],
        "currency": data["currency"],
        "market": data["market"],
        "url": data["url"],
        "is_valid_amazon_product": data["is_valid_amazon_product"],
    }
