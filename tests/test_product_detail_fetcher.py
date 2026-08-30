from exporter import export_project_bundle
from keepa_ready import build_keepa_api_request, build_keepa_payload
from product_detail_fetcher import (
    extract_detail_fields,
    build_product_url,
    is_valid_amazon_product_page,
    fetch_real_market_data_for_asin,
    enrich_candidate_with_asin_detail,
)


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class FakeSession:
    def __init__(self, html):
        self.html = html

    def get(self, url, timeout=None):
        return FakeResponse(self.html)


def test_build_product_url_uses_asin_in_amazon_domain():
    url = build_product_url('B0TEST123', market='com')
    assert 'amazon.com' in url
    assert 'B0TEST123' in url


def test_extract_detail_fields_parses_title_and_price():
    html = '''
    <html><body>
      <img src="https://example.com/image.jpg" />
      <span id="productTitle">Portable Blender</span>
      <span class="a-price-whole">29</span>
      <span class="a-price-fraction">99</span>
    </body></html>
    '''

    details = extract_detail_fields(html)
    assert details['title'] == 'Portable Blender'
    assert details['price'] == 29.99
    assert details['image_url'].endswith('image.jpg')


def test_is_valid_amazon_product_page_checks_real_product_markers():
    html = '''
    <html><body>
      <span id="productTitle">Portable Blender</span>
      <span class="a-price-whole">59</span>
      <span class="a-price-fraction">98</span>
      <div data-asin="B0TEST123"></div>
    </body></html>
    '''
    assert is_valid_amazon_product_page(html, "B0TEST123") is True
    assert is_valid_amazon_product_page("<html><body>Not Amazon</body></html>", "B0TEST123") is False


def test_fetch_real_market_data_for_asin_returns_validated_market_details():
    html = '''
    <html><body>
      <span id="productTitle">Portable Blender</span>
      <span class="a-price-whole">59</span>
      <span class="a-price-fraction">98</span>
      <img src="https://example.com/pb.jpg" />
      <div data-asin="B0TEST123"></div>
    </body></html>
    '''
    session = FakeSession(html)
    data = fetch_real_market_data_for_asin("B0TEST123", market="com", request_session=session)
    assert data["is_valid_amazon_product"] is True
    assert data["title"] == "Portable Blender"
    assert data["price"] == 59.98
    assert data["market"] == "com"


def test_enrich_candidate_with_asin_detail_and_keepa_payload_use_real_product_data():
    html = '''
    <html><body>
      <span id="productTitle">Portable Blender</span>
      <span class="a-price-whole">59</span>
      <span class="a-price-fraction">98</span>
      <img src="https://example.com/pb.jpg" />
      <div data-asin="B0TEST123"></div>
    </body></html>
    '''
    session = FakeSession(html)
    candidate = {
        "asin": "B0TEST123",
        "product_name": "Portable Blender",
        "de_price": 59.98,
        "roi": 92.0,
        "score": 70.0,
    }

    enriched = enrich_candidate_with_asin_detail(candidate, market="com", request_session=session)
    assert enriched["is_valid_amazon_product"] is True
    assert enriched["verified_title"] == "Portable Blender"
    assert enriched["verified_price"] == 59.98

    payload = build_keepa_payload(enriched)
    assert payload["asin"] == "B0TEST123"
    assert payload["verified_title"] == "Portable Blender"
    assert payload["status"] == "keepa_ready"


def test_build_keepa_api_request_and_export_bundle():
    candidate = {
        "asin": "B0TEST123",
        "product_name": "Portable Blender",
        "de_price": 59.98,
        "roi": 92.0,
        "score": 70.0,
        "verified_title": "Portable Blender",
        "verified_price": 59.98,
        "market": "com",
        "is_valid_amazon_product": True,
    }

    request = build_keepa_api_request([candidate], api_key="demo-key")
    assert request["api_key"] == "demo-key"
    assert request["market"] == "com"
    assert request["asins"][0] == "B0TEST123"
    assert request["items"][0]["verified_title"] == "Portable Blender"

    bundle_path = export_project_bundle([candidate], output_dir="reports/test_bundle")
    assert bundle_path["excel"].endswith(".xlsx")
    assert bundle_path["json"].endswith(".json")
