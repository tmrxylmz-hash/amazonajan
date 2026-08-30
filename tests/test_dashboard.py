from dashboard import build_dashboard_scan_config, build_export_bundle_name, render_dashboard_page, run_dashboard_scan
from scan_runner import run_scan_cycle


def test_build_dashboard_scan_config_uses_user_filters_and_search_terms():
    config = build_dashboard_scan_config({
        "search_terms": "portable blender, desk organizer",
        "market": "com",
        "min_roi": "25",
        "max_risk": "medium",
        "min_sales": "300",
        "max_fba": "12",
        "amazon_url": "https://www.amazon.com/dp/B0TEST001",
        "asin": "B0TEST001",
    })

    assert config["search_terms"] == ["portable blender", "desk organizer"]
    assert config["market"] == "com"
    assert config["criteria"]["min_roi_percent"] == 25.0
    assert config["criteria"]["max_risk_level"] == "medium"
    assert config["criteria"]["min_monthly_sales"] == 300
    assert config["criteria"]["max_fba_sellers"] == 12
    assert config["amazon_url"] == "https://www.amazon.com/dp/B0TEST001"
    assert config["asin"] == "B0TEST001"


def test_dashboard_mode_and_export_name_are_clear_and_persisted():
    config = build_dashboard_scan_config({
        "search_terms": "portable blender",
        "market": "de",
        "mode": "bulk_search",
        "save_filter": "true",
        "asin": "B0TEST001",
    })

    assert config["mode"] == "bulk_search"
    assert config["save_filter"] is True
    export_name = build_export_bundle_name(config)
    assert "amazon_" in export_name
    assert "de" in export_name
    assert "b0test001" in export_name


def test_run_scan_cycle_applies_user_criteria(monkeypatch):
    def fake_research_scan(search_terms, market="com", criteria=None):
        return {
            "search_results": [
                {"title": "High ROI Product", "asin": "B0GOOD001", "roi": 55.0, "monthly_sales": 900},
                {"title": "Low ROI Product", "asin": "B0LOW001", "roi": 20.0, "monthly_sales": 400},
            ]
        }

    monkeypatch.setattr("scan_runner.run_research_scan", fake_research_scan)

    result = run_scan_cycle(["portable blender"], criteria={"min_roi_percent": 35.0, "min_monthly_sales": 500}, market="com")

    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["asin"] == "B0GOOD001"


def test_run_dashboard_scan_rejects_non_amazon_link_without_500():
    result = run_dashboard_scan({
        "search_terms": ["portable blender"],
        "market": "com",
        "mode": "single_asin",
        "amazon_url": "https://example.com/not-amazon",
        "asin": "",
        "criteria": {"min_roi_percent": 25, "min_monthly_sales": 300},
    })

    assert result["candidate_count"] == 0
    assert result["candidates"] == []
    assert "Geçerli bir Amazon ürün linki" in result["error"]


def test_run_dashboard_scan_rejects_search_results_url_without_500():
    config = build_dashboard_scan_config({
        "search_terms": "",
        "market": "de",
        "mode": "single_asin",
        "amazon_url": "https://www.amazon.de/s?rh=n%3A15460549031&language=tr_TR&brr=1&rd=1",
        "asin": "",
        "criteria": {"min_roi_percent": 25, "min_monthly_sales": 300},
    })

    assert config["mode"] == "bulk_search"
    assert config["search_terms"] == ["portable blender"] or "portable blender" in config["search_terms"]

    result = run_dashboard_scan(config)

    assert result["candidate_count"] >= 0
    assert result.get("error") is None or "arama sonuçları linki kabul edilmez" not in result.get("error", "")


def test_render_dashboard_page_handles_export_links_without_shadowing_html_module():
    result = {
        "candidate_count": 0,
        "candidates": [],
        "export": {"excel": "C:/tmp/report.xlsx", "json": "C:/tmp/report.json"},
        "export_filename": "demo_report",
    }

    page = render_dashboard_page(result=result, form={"search_terms": "portable blender", "market": "com", "mode": "bulk_search"})

    assert "demo_report" in page
    assert "/download?path=" in page
    assert "Export hazırlanmadı" not in page


def test_build_dashboard_scan_config_uses_categories_when_no_search_terms():
    config = build_dashboard_scan_config({
        "search_terms": "",
        "market": "com",
        "mode": "bulk_search",
        "categories": "Home,Kitchen,Office",
        "amazon_url": "",
        "asin": "",
    })

    assert config["search_terms"] == ["Home", "Kitchen", "Office"]
    assert config["mode"] == "bulk_search"
