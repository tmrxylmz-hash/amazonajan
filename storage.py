import sqlite3
from pathlib import Path


def create_candidates_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            asin TEXT,
            us_price REAL,
            de_price REAL,
            monthly_sales INTEGER,
            roi REAL,
            score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def ensure_db(path: str = "data/amazon_ai_ajan.db") -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    create_candidates_table(conn)
    return conn


def save_candidates(conn, candidates):
    create_candidates_table(conn)
    for item in candidates:
        conn.execute(
            """
            INSERT INTO candidates (product_name, asin, us_price, de_price, monthly_sales, roi, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("product_name"),
                item.get("asin"),
                item.get("us_price"),
                item.get("de_price"),
                item.get("monthly_sales"),
                item.get("roi"),
                item.get("score"),
            ),
        )
    conn.commit()


def load_candidates(conn):
    rows = conn.execute(
        """
        SELECT product_name, asin, us_price, de_price, monthly_sales, roi, score
        FROM candidates
        ORDER BY id DESC
        """
    ).fetchall()
    return [
        {
            "product_name": row[0],
            "asin": row[1],
            "us_price": row[2],
            "de_price": row[3],
            "monthly_sales": row[4],
            "roi": row[5],
            "score": row[6],
        }
        for row in rows
    ]
