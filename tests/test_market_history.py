from market_history import add_history_snapshot, build_history_report, load_history


def test_history_snapshot_is_stored_and_reported():
    history = []
    add_history_snapshot(history, {
        'asin': 'B0HIST1',
        'product_name': 'Portable Blender',
        'de_price': 59.98,
        'roi': 88.0,
        'score': 68.0,
    })

    report = build_history_report(history)

    assert len(report) == 1
    assert report[0]['asin'] == 'B0HIST1'
    assert report[0]['de_price'] == 59.98


def test_load_history_returns_list():
    history = load_history()
    assert isinstance(history, list)
