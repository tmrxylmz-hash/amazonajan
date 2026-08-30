from pathlib import Path
import json

HISTORY_PATH = Path("data/market_history.json")


def ensure_history_file():
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]", encoding="utf-8")


def load_history():
    ensure_history_file()
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def add_history_snapshot(history_list, snapshot):
    history_list.append({
        "asin": snapshot.get("asin"),
        "product_name": snapshot.get("product_name"),
        "de_price": snapshot.get("de_price"),
        "roi": snapshot.get("roi"),
        "score": snapshot.get("score"),
    })
    return history_list


def save_history(history_list):
    ensure_history_file()
    HISTORY_PATH.write_text(json.dumps(history_list, indent=2), encoding="utf-8")


def build_history_report(history_list):
    return [
        {
            "asin": item.get("asin"),
            "product_name": item.get("product_name"),
            "de_price": item.get("de_price"),
            "roi": item.get("roi"),
            "score": item.get("score"),
        }
        for item in history_list
    ]
