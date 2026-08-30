from monitoring import compare_candidates_with_history


def test_compare_candidates_with_history_detects_change():
    current = [
        {"asin": "B0M1", "product_name": "Portable Blender", "de_price": 64.99, "roi": 120.0, "score": 82.0},
    ]
    history = [
        {"asin": "B0M1", "product_name": "Portable Blender", "de_price": 59.98, "roi": 88.0, "score": 68.0},
    ]

    changes = compare_candidates_with_history(current, history)

    assert len(changes) == 1
    assert changes[0]["asin"] == "B0M1"
    assert changes[0]["de_price_change"] > 0
    assert changes[0]["roi_change"] > 0
