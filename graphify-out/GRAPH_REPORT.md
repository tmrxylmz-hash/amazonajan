# Graph Report - Amazon_AI_Ajan  (2026-08-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 158 nodes · 360 edges · 9 communities (7 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- main.py
- research_engine.py
- dashboard.py
- search_provider.py
- test_product_detail_fetcher.py
- run_scan_cycle
- test_market_analysis.py
- ScanScheduler
- extract_product_details

## God Nodes (most connected - your core abstractions)
1. `run_project_cycle()` - 14 edges
2. `run_scan_cycle()` - 13 edges
3. `score_candidate()` - 11 edges
4. `ProductCandidate` - 10 edges
5. `export_project_bundle()` - 9 edges
6. `render_dashboard_page()` - 9 edges
7. `build_real_source_plan()` - 9 edges
8. `fetch_search_results()` - 9 edges
9. `fetch_real_market_data_for_asin()` - 9 edges
10. `build_keepa_api_request()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `load_demo_candidates()` --calls--> `ProductCandidate`  [EXTRACTED]
  data_sources.py → models.py
- `run_dashboard_scan()` --calls--> `export_project_bundle()`  [EXTRACTED]
  dashboard.py → exporter.py
- `test_enrich_candidate_with_asin_detail_and_keepa_payload_use_real_product_data()` --calls--> `build_keepa_payload()`  [EXTRACTED]
  tests/test_product_detail_fetcher.py → keepa_ready.py
- `run_project_cycle()` --calls--> `enrich_candidate_with_asin_detail()`  [EXTRACTED]
  main.py → product_detail_fetcher.py
- `run_project_cycle()` --calls--> `run_scan_cycle()`  [EXTRACTED]
  main.py → scan_runner.py

## Import Cycles
- None detected.

## Communities (9 total, 2 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.16
Nodes (22): Connection, export_candidates_report(), export_project_bundle(), build_keepa_api_request(), build_keepa_payload(), save_keepa_queue(), run_project_cycle(), add_history_snapshot() (+14 more)

### Community 1 - "research_engine.py"
Cohesion: 0.17
Nodes (16): generate_ai_summary(), load_demo_candidates(), filter_candidates(), passes_criteria(), ProductCandidate, build_research_report(), score_candidate(), _score_competition() (+8 more)

### Community 2 - "dashboard.py"
Cohesion: 0.16
Nodes (19): BaseHTTPRequestHandler, build_dashboard_scan_config(), build_export_bundle_name(), _build_export_links(), _build_status_message(), _build_summary_cards(), _clean_list(), DashboardRequestHandler (+11 more)

### Community 3 - "search_provider.py"
Cohesion: 0.15
Nodes (17): build_amazon_search_url(), build_real_source_plan(), build_request_session(), build_amazon_search_url(), build_search_fallback_urls(), build_web_fallback_url(), extract_amazon_result_cards(), extract_web_fallback_results() (+9 more)

### Community 4 - "test_product_detail_fetcher.py"
Cohesion: 0.21
Nodes (13): build_product_url(), enrich_candidate_with_asin_detail(), extract_detail_fields(), fetch_product_details(), fetch_real_market_data_for_asin(), is_valid_amazon_product_page(), FakeResponse, FakeSession (+5 more)

### Community 5 - "run_scan_cycle"
Cohesion: 0.26
Nodes (12): build_amazon_de_search_url(), calculate_competition_score(), compare_market_pair(), run_research_scan(), deduplicate_candidates(), run_scan_cycle(), test_run_scan_cycle_applies_user_criteria(), test_build_amazon_de_search_url_uses_asin_keyword() (+4 more)

### Community 6 - "test_market_analysis.py"
Cohesion: 0.54
Nodes (6): analyze_candidate(), calculate_profit(), estimate_de_price(), test_analyze_candidate_returns_profit_and_roi_for_us_to_de_flow(), test_calculate_profit_uses_basic_fee_model(), test_estimate_de_price_uses_reasonable_euro_multiplier()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_scan_cycle()` connect `run_scan_cycle` to `main.py`, `dashboard.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `fetch_search_results()` connect `search_provider.py` to `research_engine.py`, `run_scan_cycle`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `run_research_scan()` connect `run_scan_cycle` to `research_engine.py`, `search_provider.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._