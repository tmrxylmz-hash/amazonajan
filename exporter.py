from pathlib import Path


def export_candidates_report(candidates, output_path: str = "reports/amazon_candidates.xlsx") -> str:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl kurulu değil. 'pip install openpyxl' çalıştırın.") from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "AmazonCandidates"
    headers = [
        "Product",
        "ASIN",
        "US Price",
        "DE Price",
        "Monthly Sales",
        "FBA Sellers",
        "Amazon Seller",
        "Profit",
        "ROI",
        "Risk",
        "Score",
        "AI Summary",
    ]
    sheet.append(headers)

    for candidate in candidates:
        sheet.append(
            [
                candidate.get("product_name", ""),
                candidate.get("asin", ""),
                candidate.get("us_price", ""),
                candidate.get("de_price", ""),
                candidate.get("monthly_sales", ""),
                candidate.get("fba_sellers", ""),
                candidate.get("amazon_seller", ""),
                candidate.get("profit", ""),
                candidate.get("roi", ""),
                candidate.get("risk_level", ""),
                candidate.get("score", ""),
                candidate.get("ai_summary", ""),
            ]
        )

    for cell in sheet[1]:
        cell.font = cell.font.copy(bold=True)

    sheet.freeze_panes = "A2"
    workbook.save(path)
    return str(path)


def export_project_bundle(candidates, output_dir: str = "reports", include_json: bool = True, api_key: str = "") -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    excel_path = output_path / "amazon_candidates_bundle.xlsx"
    json_path = output_path / "amazon_candidates_bundle.json"

    export_candidates_report(candidates, output_path=str(excel_path))

    if include_json:
        from keepa_ready import build_keepa_api_request
        payload = build_keepa_api_request(candidates, api_key=api_key, market="com")
        json_path.write_text(str(payload), encoding="utf-8")

    return {
        "excel": str(excel_path),
        "json": str(json_path),
    }
