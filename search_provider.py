import re
from urllib.parse import quote_plus

import requests

from data_sources import (
    build_amazon_search_url as build_amazon_search_url_source,
    build_real_source_plan,
    build_request_session,
)


def build_amazon_search_url(keyword: str, market: str = "com") -> str:
    return build_amazon_search_url_source(keyword, market)


def build_web_fallback_url(keyword: str) -> str:
    return build_real_source_plan(keyword)[1]["url"]


def build_search_fallback_urls(keyword: str) -> list[str]:
    return [item["url"] for item in build_real_source_plan(keyword)[1:]]


def _is_generic_amazon_title(title: str) -> bool:
    cleaned = " ".join(str(title or "").split()).strip()
    if not cleaned:
        return True
    lowered = cleaned.lower()
    generic_markers = (
        "add to cart",
        "overall pick",
        "see details",
        "shop now",
        "buy now",
        "view details",
        "details",
        "amazon prime",
        "featured",
        "related product",
    )
    return lowered in generic_markers or any(marker in lowered for marker in generic_markers)


def extract_amazon_result_cards(html: str):
    results = []
    pattern = re.compile(r'<div[^>]*data-asin="([A-Za-z0-9]+)"[^>]*>(.*?)</div>', re.DOTALL)
    matches = pattern.findall(html)

    for asin, block in matches:
        title_match = re.search(r'<span[^>]*class="[^"]*a-text-normal[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not title_match:
            title_match = re.search(r'<span[^>]*>(.*?)</span>', block, re.DOTALL)
        title = re.sub(r'<.*?>', '', title_match.group(1)) if title_match else ""
        title = " ".join(title.split()).strip()
        if asin and title and not _is_generic_amazon_title(title):
            results.append({"asin": asin, "title": title})

    return results


def extract_web_fallback_results(html: str):
    results = []
    link_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    for href, content in link_pattern.findall(html):
        text = re.sub(r'<.*?>', '', content)
        text = ' '.join(text.split())
        if not text:
            continue
        if "result" in href.lower() or "duckduckgo" in href.lower() or "bing" in href.lower() or "google" in href.lower():
            continue
        title = text.title()
        results.append({
            "asin": re.sub(r'[^A-Za-z0-9]', '', href)[:12] or "WEBFALLBACK",
            "title": title,
            "url": href,
        })
    return results[:8] if results else [{"asin": "WEBFALLBACK", "title": "Search Result", "url": ""}]


def fetch_search_results(keyword: str, market: str = "com", request_session=None):
    amazon_url = build_amazon_search_url(keyword, market)
    fallback_urls = build_search_fallback_urls(keyword)

    def request(url):
        if request_session is None:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            response = session.get(url, timeout=20)
        else:
            response = request_session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    try:
        html = request(amazon_url)
        results = extract_amazon_result_cards(html)
        if results:
            return {
                "url": amazon_url,
                "results": results,
                "keyword": keyword,
                "market": market,
                "source": "amazon",
            }
    except Exception:
        pass

    for fallback_url in fallback_urls:
        try:
            html = request(fallback_url)
            results = extract_web_fallback_results(html)
            if results:
                return {
                    "url": fallback_url,
                    "results": results,
                    "keyword": keyword,
                    "market": market,
                    "source": "web_fallback",
                }
        except Exception:
            continue

    return {
        "url": "",
        "results": [],
        "keyword": keyword,
        "market": market,
        "source": "blocked",
    }
