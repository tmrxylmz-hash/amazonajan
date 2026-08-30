import requests

from search_provider import (
    build_amazon_search_url,
    extract_amazon_result_cards,
    fetch_search_results,
)


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"fake http error {self.status_code}")


class FakeSession:
    def __init__(self, amazon_error=True):
        self.amazon_error = amazon_error

    def get(self, url, timeout=None):
        if "amazon.com" in url or "amazon.de" in url:
            if self.amazon_error:
                raise requests.HTTPError("amazon blocked")
            return FakeResponse("<div data-asin=\"B0FALLBACK\"><span>Fallback Product</span></div>")
        if "duckduckgo.com" in url:
            return FakeResponse("""
                <html><body>
                <div class="result-link"><a href="https://example.com/product/portable-blender">Portable Blender Review</a></div>
                <div class="result-link"><a href="https://example.com/product/desk-organizer">Desk Organizer Guide</a></div>
                </body></html>
            """)
        raise RuntimeError(f"unsupported url: {url}")


def test_build_amazon_search_url_uses_market_specific_domain():
    url = build_amazon_search_url("portable blender", market="com")
    assert "amazon.com/s" in url
    assert "portable+blender" in url

    url_de = build_amazon_search_url("portable blender", market="de")
    assert "amazon.de/s" in url_de


def test_extract_amazon_result_cards_parses_asin_and_title():
    sample_html = """
    <html><body>
    <div data-asin="B0TEST123">
      <a href="/gp/product/B0TEST123">
        <span class="a-size-base-plus a-color-base a-text-normal">Portable Blender</span>
      </a>
    </div>
    <div data-asin="B0TEST456">
      <a href="/gp/product/B0TEST456">
        <span class="a-size-base-plus a-color-base a-text-normal">Desk Organizer</span>
      </a>
    </div>
    </body></html>
    """

    results = extract_amazon_result_cards(sample_html)

    assert len(results) == 2
    assert results[0]["asin"] == "B0TEST123"
    assert "Portable Blender" in results[0]["title"]


def test_fetch_search_results_falls_back_when_amazon_blocks():
    session = FakeSession(amazon_error=True)
    result = fetch_search_results("portable blender", request_session=session)

    assert result["source"] == "web_fallback"
    assert len(result["results"]) >= 1
    assert "Portable Blender" in result["results"][0]["title"]


def test_extract_amazon_result_cards_ignores_generic_button_texts():
    sample_html = '''
    <html><body>
      <div data-asin="B0GOOD001">
        <span class="a-text-normal">Portable Blender</span>
      </div>
      <div data-asin="B0BUTTON001">
        <span class="a-text-normal">Add to cart</span>
      </div>
      <div data-asin="B0BAD002">
        <span class="a-text-normal">Overall Pick</span>
      </div>
    </body></html>
    '''

    results = extract_amazon_result_cards(sample_html)

    assert len(results) == 1
    assert results[0]["asin"] == "B0GOOD001"
    assert "Portable Blender" in results[0]["title"]
