from urllib.parse import quote_plus

import requests

from models import ProductCandidate


def build_request_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    return session


def build_amazon_search_url(keyword: str, market: str = "com") -> str:
    market_map = {
        "com": "https://www.amazon.com/s?k={keyword}",
        "de": "https://www.amazon.de/s?k={keyword}",
    }
    domain = market_map.get(market.lower(), market_map["com"])
    return domain.format(keyword=quote_plus(keyword))


def build_real_source_plan(keyword: str, market: str = "com") -> list[dict]:
    encoded_keyword = quote_plus(keyword)
    amazon_url = build_amazon_search_url(keyword, market)
    return [
        {"source": "amazon_search", "url": amazon_url},
        {"source": "duckduckgo", "url": f"https://duckduckgo.com/html/?q={encoded_keyword}"},
        {"source": "bing", "url": f"https://www.bing.com/search?q={encoded_keyword}"},
        {"source": "google", "url": f"https://www.google.com/search?q={encoded_keyword}"},
    ]


def load_demo_candidates() -> list[ProductCandidate]:
    return [
        ProductCandidate(
            product_name="Portable Blender",
            asin="B0TEST001",
            us_price=19.99,
            de_price=52.99,
            monthly_sales=1800,
            fba_sellers=4,
            amazon_seller=False,
            estimated_profit=12.0,
            estimated_roi=58.0,
            risk_level="low",
            category="Kitchen",
            image_url="https://example.com/img1.png",
        ),
        ProductCandidate(
            product_name="Desk Organizer",
            asin="B0TEST002",
            us_price=22.5,
            de_price=48.0,
            monthly_sales=900,
            fba_sellers=11,
            amazon_seller=False,
            estimated_profit=7.5,
            estimated_roi=34.0,
            risk_level="medium",
            category="Office",
            image_url="https://example.com/img2.png",
        ),
        ProductCandidate(
            product_name="Unsafe Item",
            asin="B0TEST003",
            us_price=35.0,
            de_price=90.0,
            monthly_sales=110,
            fba_sellers=18,
            amazon_seller=True,
            estimated_profit=2.0,
            estimated_roi=8.0,
            risk_level="high",
            category="Hazmat",
            image_url="https://example.com/img3.png",
        ),
        ProductCandidate(
            product_name="Water Bottle",
            asin="B0TEST004",
            us_price=12.5,
            de_price=29.0,
            monthly_sales=600,
            fba_sellers=8,
            amazon_seller=False,
            estimated_profit=6.2,
            estimated_roi=27.0,
            risk_level="medium",
            category="Home",
            image_url="https://example.com/img4.png",
        ),
        ProductCandidate(
            product_name="Pet Grooming Brush",
            asin="B0TEST005",
            us_price=16.0,
            de_price=38.5,
            monthly_sales=1100,
            fba_sellers=6,
            amazon_seller=False,
            estimated_profit=8.5,
            estimated_roi=44.0,
            risk_level="low",
            category="Pet",
            image_url="https://example.com/img5.png",
        ),
    ]
