import sqlite3

from storage import save_candidates, load_candidates


def test_save_and_load_candidates_round_trip():
    conn = sqlite3.connect(':memory:')
    candidates = [
        {
            'product_name': 'Portable Blender',
            'asin': 'B0TEST1',
            'us_price': 24.99,
            'de_price': 59.98,
            'monthly_sales': 1200,
            'roi': 88.0,
            'score': 68.0,
        }
    ]

    save_candidates(conn, candidates)
    loaded = load_candidates(conn)

    assert len(loaded) == 1
    assert loaded[0]['product_name'] == 'Portable Blender'
    assert loaded[0]['asin'] == 'B0TEST1'
