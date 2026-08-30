from dashboard import start_dashboard_server
from exporter import export_candidates_report, export_project_bundle
from keepa_ready import build_keepa_api_request, save_keepa_queue
from market_history import add_history_snapshot, build_history_report, load_history, save_history
from monitoring import compare_candidates_with_history
from product_detail_fetcher import enrich_candidate_with_asin_detail
from scan_runner import run_scan_cycle
from scheduler import scheduled_scan
from storage import ensure_db, save_candidates, load_candidates


def run_project_cycle():
    print("Amazon AI Ajanı çalışıyor!")
    print("\nOtomatik tarama döngüsü başlatıldı...\n")

    cycle = run_scan_cycle(["portable blender", "desk organizer", "water bottle"])
    candidates = cycle["candidates"]

    history = load_history()
    for item in candidates:
        add_history_snapshot(history, {
            "asin": item.get("asin"),
            "product_name": item.get("product_name"),
            "de_price": item.get("de_price"),
            "roi": item.get("roi"),
            "score": item.get("score"),
        })
    save_history(history)

    changes = compare_candidates_with_history(candidates, history)
    if changes:
        print("\nPiyasa değişim tespiti:")
        for change in changes:
            print(
                f"- {change['product_name']} | ASIN: {change['asin']} | "
                f"Fiyat değişimi: €{change['de_price_change']} | ROI değişimi: {change['roi_change']}% | Skor değişimi: {change['score_change']}"
            )

    detail_results = []
    enriched_candidates = []
    for item in candidates:
        if item.get("asin") and item["asin"] != "html":
            try:
                enriched = enrich_candidate_with_asin_detail(item, market="com")
                enriched_candidates.append(enriched)
                detail_results.append({
                    "asin": item["asin"],
                    "title": enriched.get("verified_title", item["product_name"]),
                    "price": enriched.get("verified_price", item.get("de_price")),
                    "image_url": enriched.get("verified_image_url", ""),
                    "is_valid_amazon_product": enriched.get("is_valid_amazon_product", False),
                })
            except Exception:
                enriched_candidates.append({**item, "is_valid_amazon_product": False})
                detail_results.append({
                    "asin": item["asin"],
                    "title": item["product_name"],
                    "price": 0.0,
                    "image_url": "",
                    "is_valid_amazon_product": False,
                })

    if enriched_candidates:
        keepa_request = build_keepa_api_request(enriched_candidates, api_key="demo-key", market="com")
        print(f"Keepa API request hazır: {len(keepa_request['asins'])} ASIN")

    if not candidates:
        print("Hiç uygun aday bulunamadı.")
    else:
        for item in candidates:
            print(
                f"- {item['product_name']} | ASIN: {item['asin']} | "
                f"DE Fiyat: €{item['de_price']} | ROI: {item['roi']}% | Puan: {item['score']}"
            )

    conn = ensure_db()
    save_candidates(conn, candidates)
    stored = load_candidates(conn)
    print(f"\nVeritabanında saklanan aday sayısı: {len(stored)}")
    print(f"Piyasa geçmişi kayıt sayısı: {len(build_history_report(history))}")

    keepa_path = save_keepa_queue(enriched_candidates or candidates)
    print(f"Keepa hazır kuyruk dosyası: {keepa_path}")

    bundle = export_project_bundle(enriched_candidates or candidates, output_dir="reports", api_key="demo-key")
    print(f"\nExcel raporu oluşturuldu: {bundle['excel']}")
    print(f"JSON export oluşturuldu: {bundle['json']}")
    return detail_results


if __name__ == "__main__":
    print("Amazon AI Ajan başlatılıyor... Dashboard için http://127.0.0.1:8000 adresini açın.")
    start_dashboard_server()
