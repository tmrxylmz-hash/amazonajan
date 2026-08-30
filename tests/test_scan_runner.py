from scan_runner import deduplicate_candidates, run_scan_cycle


def test_deduplicate_candidates_keeps_highest_score_for_same_asin():
    candidates = [
        {"asin": "B0A", "score": 50, "product_name": "Low"},
        {"asin": "B0A", "score": 90, "product_name": "High"},
        {"asin": "B0B", "score": 70, "product_name": "Other"},
    ]

    deduped = deduplicate_candidates(candidates)

    assert len(deduped) == 2
    assert deduped[0]["product_name"] == "High"
    assert deduped[1]["product_name"] == "Other"


def test_run_scan_cycle_returns_scan_summary_and_deduplicated_candidates():
    cycle = run_scan_cycle(["portable blender", "water bottle"])

    assert cycle["search_terms"] == ["portable blender", "water bottle"]
    assert "candidates" in cycle
    assert isinstance(cycle["candidate_count"], int)
