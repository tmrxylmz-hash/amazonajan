from data_sources import build_request_session, build_real_source_plan


def test_build_request_session_adds_browser_headers():
    session = build_request_session()
    assert "Mozilla/5.0" in session.headers["User-Agent"]
    assert session.headers["Accept-Language"]
    assert session.headers["Accept"]


def test_build_real_source_plan_returns_amazon_priority_with_fallbacks():
    plan = build_real_source_plan("portable blender", market="com")
    assert len(plan) >= 3
    assert plan[0]["source"] == "amazon_search"
    assert any(item["source"] == "duckduckgo" for item in plan)
    assert any(item["source"] == "bing" for item in plan)
