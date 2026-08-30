import html
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from exporter import export_project_bundle
from product_detail_fetcher import enrich_candidate_with_asin_detail, fetch_product_details
from scan_runner import run_scan_cycle


def _parse_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _clean_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        flat = []
        for item in value:
            flat.extend(_clean_list(item))
        return flat
    return [item.strip() for item in str(value).replace("\n", ",").split(",") if item.strip()]


def _as_text(value, default=""):
    if value is None:
        return default
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _extract_asin_from_url(url: str) -> str:
    if not url:
        return ""
    import re
    match = re.search(r"(?:dp|gp/product|asin=)([A-Z0-9]{10})", url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return ""


def _is_amazon_search_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "amazon." not in host:
        return False
    path = (parsed.path or "").lower()
    if "/s" in path or "/gp/search" in path:
        return True
    query = parsed.query.lower()
    return "k=" in query or "field-keywords" in query or "keywords=" in query


def _extract_search_terms_from_url(url: str):
    if not url:
        return []
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    candidates = []
    for key in ("k", "keywords", "field-keywords", "q"):
        if key in query:
            for value in query[key]:
                term_values = _clean_list(value.replace("+", " "))
                for term in term_values:
                    if term.lower() not in {"/s", "/gp/search", "s"}:
                        candidates.append(term)
    if candidates:
        return candidates
    if "amazon." not in ((parsed.netloc or "").lower()):
        return []
    path = (parsed.path or "").strip("/")
    if not path or path in {"s", "gp", "gp/search"}:
        return []
    return _clean_list(path)


def _slugify(value: str, max_length: int = 14) -> str:
    cleaned = ''.join(ch.lower() if ch.isalnum() else '_' for ch in str(value or '').strip())
    cleaned = cleaned.strip('_')
    return cleaned[:max_length] if cleaned else 'dashboard'


def build_export_bundle_name(config: dict) -> str:
    search_terms = config.get('search_terms') or ['portable blender']
    market = (config.get('market') or 'com').lower()
    mode = (config.get('mode') or 'bulk_search').lower()
    seed = _slugify(search_terms[0])
    if config.get('asin'):
        seed = _slugify(config.get('asin'))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"amazon_{mode}_{market}_{seed}_{timestamp}"


def load_saved_filters() -> dict:
    path = Path('data/dashboard_filters.json')
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_filter_config(config: dict):
    path = Path('data/dashboard_filters.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'search_terms': config.get('search_terms', ['portable blender']),
        'market': config.get('market', 'com'),
        'mode': config.get('mode', 'bulk_search'),
        'min_roi': config.get('criteria', {}).get('min_roi_percent', 25),
        'max_risk': config.get('criteria', {}).get('max_risk_level', 'medium'),
        'min_sales': config.get('criteria', {}).get('min_monthly_sales', 300),
        'max_fba': config.get('criteria', {}).get('max_fba_sellers', 12),
        'categories': config.get('criteria', {}).get('product_categories', ['Home', 'Kitchen', 'Office']),
        'amazon_url': config.get('amazon_url', ''),
        'asin': config.get('asin', ''),
        'exclude_hazmat': config.get('criteria', {}).get('exclude_hazmat', True),
        'prefer_no_amazon_seller': config.get('criteria', {}).get('prefer_no_amazon_seller', True),
    }
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def build_dashboard_scan_config(form_data: dict) -> dict:
    amazon_url = (form_data.get('amazon_url') or '').strip()
    categories = _clean_list(form_data.get('categories'))
    search_terms = _clean_list(form_data.get('search_terms'))
    if not search_terms and amazon_url and _is_amazon_search_url(amazon_url):
        search_terms = _extract_search_terms_from_url(amazon_url)
    if not search_terms and categories:
        search_terms = categories
    if not search_terms and form_data.get('asin'):
        search_terms = []
    if not search_terms:
        search_terms = ['portable blender']

    criteria = {
        'min_roi_percent': float(form_data.get('min_roi') or 25.0),
        'max_risk_level': (form_data.get('max_risk') or 'medium').lower(),
        'min_monthly_sales': int(form_data.get('min_sales') or 300),
        'max_fba_sellers': int(form_data.get('max_fba') or 12),
        'target_currency': 'EUR',
        'product_categories': categories or ['Home', 'Kitchen', 'Office'],
        'exclude_hazmat': _parse_bool(form_data.get('exclude_hazmat')),
        'prefer_no_amazon_seller': _parse_bool(form_data.get('prefer_no_amazon_seller')),
    }

    asin = (form_data.get('asin') or '').strip().upper()
    if not asin and amazon_url:
        asin = _extract_asin_from_url(amazon_url)

    mode = (form_data.get('mode') or 'bulk_search').lower()
    if amazon_url and _is_amazon_search_url(amazon_url):
        mode = 'bulk_search'

    config = {
        'search_terms': search_terms,
        'market': (form_data.get('market') or 'com').lower(),
        'mode': mode,
        'criteria': criteria,
        'amazon_url': amazon_url,
        'asin': asin,
        'save_filter': _parse_bool(form_data.get('save_filter')),
    }
    if config['mode'] == 'single_asin' and not config['asin'] and config['amazon_url'] and not _is_amazon_search_url(config['amazon_url']):
        config['asin'] = _extract_asin_from_url(config['amazon_url'])
    if config['amazon_url'] and _is_amazon_search_url(config['amazon_url']):
        config['mode'] = 'bulk_search'
        config['search_terms'] = _extract_search_terms_from_url(config['amazon_url']) or config['search_terms']
    return config


def run_dashboard_scan(config: dict) -> dict:
    search_terms = _clean_list(config.get("search_terms")) or ["portable blender"]
    categories = _clean_list(config.get("criteria", {}).get("product_categories")) or _clean_list(config.get("categories"))
    criteria = config.get("criteria") or {}
    asin = (config.get("asin") or "").strip().upper()
    amazon_url = (config.get("amazon_url") or "").strip()
    mode = (config.get("mode") or "bulk_search").lower()
    extracted_asin = asin or _extract_asin_from_url(amazon_url)

    if amazon_url and _is_amazon_search_url(amazon_url):
        search_terms = _extract_search_terms_from_url(amazon_url) or search_terms
        mode = "bulk_search"
        asin = ""
        extracted_asin = ""

    has_any_input = bool(search_terms) or bool(amazon_url) or bool(asin) or bool(categories)
    if not has_any_input:
        return {
            "search_terms": search_terms,
            "criteria": criteria,
            "candidates": [],
            "candidate_count": 0,
            "amazon_url": amazon_url,
            "asin": asin,
            "mode": mode,
            "error": "Arama terimi, Amazon linki, ASIN veya kategori alanlarından en az biri zorunludur.",
        }

    if (mode == "single_asin" or asin or amazon_url) and not extracted_asin and not (amazon_url and _is_amazon_search_url(amazon_url)):
        if amazon_url and "amazon." in amazon_url.lower():
            message = "Bu bir Amazon ürün detay sayfası değil; arama sonuçları linki kabul edilmez. Lütfen ASIN veya /dp/ biçiminde ürün linki girin."
        else:
            message = "Geçerli bir Amazon ürün linki veya ASIN girmeniz gerekiyor."
        return {
            "search_terms": search_terms,
            "criteria": criteria,
            "candidates": [],
            "candidate_count": 0,
            "amazon_url": amazon_url,
            "asin": asin,
            "mode": mode,
            "error": message,
        }

    if mode == "single_asin" or asin:
        try:
            detail = fetch_product_details(extracted_asin, market=config.get("market", "com"))
            candidate = {
                "product_name": detail.get("title") or "Custom ASIN candidate",
                "asin": extracted_asin,
                "us_price": detail.get("price") or 0.0,
                "de_price": detail.get("price") or 0.0,
                "monthly_sales": criteria.get("min_monthly_sales", 300),
                "roi": criteria.get("min_roi_percent", 25.0),
                "score": 90,
                "source": "dashboard_single_asin",
                "url": amazon_url or detail.get("url"),
                "market": config.get("market", "com"),
                "amazon_url": amazon_url,
            }
            enriched = enrich_candidate_with_asin_detail(candidate, market=config.get("market", "com"))
            export_bundle = export_project_bundle([enriched], output_dir="reports", api_key="demo-key")
            result = {
                "search_terms": search_terms,
                "criteria": criteria,
                "candidates": [enriched],
                "candidate_count": 1,
                "amazon_url": amazon_url,
                "asin": extracted_asin,
                "mode": mode,
                "export": export_bundle,
            }
            result['export_filename'] = build_export_bundle_name(config)
            return result
        except Exception as exc:
            return {
                "search_terms": search_terms,
                "criteria": criteria,
                "candidates": [],
                "candidate_count": 0,
                "amazon_url": amazon_url,
                "asin": extracted_asin,
                "mode": mode,
                "error": str(exc),
            }

    cycle = run_scan_cycle(search_terms, criteria=criteria, market=config.get("market", "com"))
    filtered = []
    for item in cycle.get("candidates", []):
        roi = float(item.get("roi") or 0)
        if roi < float(criteria.get("min_roi_percent", 0)):
            continue
        if int(item.get("monthly_sales") or 0) < int(criteria.get("min_monthly_sales", 0)):
            continue
        filtered.append(item)

    selected = filtered or cycle.get("candidates", [])
    export_bundle = export_project_bundle(selected, output_dir="reports", api_key="demo-key")
    result = {
        "search_terms": search_terms,
        "criteria": criteria,
        "candidates": selected,
        "candidate_count": len(selected),
        "amazon_url": amazon_url,
        "asin": asin,
        "mode": mode,
        "export": export_bundle,
    }
    result['export_filename'] = build_export_bundle_name(config)
    return result


def _render_candidate_rows(candidates):
    if not candidates:
        return "<tr><td colspan='10'>Sonuç bulunamadı.</td></tr>"

    rows = []
    for item in candidates:
        product_name = str(item.get("product_name") or "-")
        asin = str(item.get("asin") or "-")
        market = str(item.get("market") or "com")
        de_price = str(item.get("de_price") or "0.00")
        roi = str(item.get("roi") or "0.0")
        score = str(item.get("score") or "0")
        source = str(item.get("source") or "search")
        amazon_url = str(item.get("url") or item.get("amazon_url") or "-")
        verified_title = str(item.get("verified_title") or item.get("product_name") or "-")

        rows.append(
            """
            <tr>
              <td><a href="{amazon_url}" target="_blank" rel="noopener noreferrer">{product_name}</a></td>
              <td>{asin}</td>
              <td>{market}</td>
              <td>{de_price}</td>
              <td>{roi}%</td>
              <td>{score}</td>
              <td>{source}</td>
              <td><a href="{amazon_url}" target="_blank" rel="noopener noreferrer">Link</a></td>
              <td>{verified_title}</td>
            </tr>
            """.format(
                product_name=html.escape(product_name),
                asin=html.escape(asin),
                market=html.escape(market),
                de_price=html.escape(de_price),
                roi=html.escape(roi),
                score=html.escape(score),
                source=html.escape(source),
                amazon_url=html.escape(amazon_url),
                verified_title=html.escape(verified_title),
            )
        )
    return "\n".join(rows)


def _build_summary_cards(result):
    candidates = result.get("candidates", [])
    if not candidates:
        return """
        <div class='card muted'>
          <div class='label'>Bakım gerekiyor</div>
          <div class='value'>0</div>
          <div class='meta'>Henüz uygun aday yok</div>
        </div>
        """

    avg_roi = sum(float(item.get("roi") or 0) for item in candidates) / len(candidates)
    avg_score = sum(float(item.get("score") or 0) for item in candidates) / len(candidates)
    high_roi = sum(1 for item in candidates if float(item.get("roi") or 0) >= 25)
    valid_asins = sum(1 for item in candidates if item.get("asin") and str(item.get("asin")).upper() != "HTML")

    return """
    <div class='card'>
      <div class='label'>Toplam aday</div>
      <div class='value'>{total}</div>
      <div class='meta'>İşlenmiş ürün sayısı</div>
    </div>
    <div class='card'>
      <div class='label'>Ortalama ROI</div>
      <div class='value'>{avg_roi:.1f}%</div>
      <div class='meta'>Kar potansiyeli</div>
    </div>
    <div class='card'>
      <div class='label'>Ortalama skor</div>
      <div class='value'>{avg_score:.1f}</div>
      <div class='meta'>Güçlü aday skoru</div>
    </div>
    <div class='card'>
      <div class='label'>Yüksek ROI</div>
      <div class='value'>{high_roi}</div>
      <div class='meta'>25% üstü adaylar</div>
    </div>
    <div class='card'>
      <div class='label'>ASIN verisi</div>
      <div class='value'>{valid_asins}</div>
      <div class='meta'>Doğrulanmış ürün sayısı</div>
    </div>
    """.format(
        total=len(candidates),
        avg_roi=avg_roi,
        avg_score=avg_score,
        high_roi=high_roi,
        valid_asins=valid_asins,
    )


def _build_export_links(result):
    export = result.get("export")
    if not export:
        return "<div class='export-wrap'><span class='chip'>Export hazırlanmadı</span></div>"
    excel = export.get("excel")
    json_path = export.get("json")
    links_html = []
    file_label = result.get('export_filename') or 'amazon_export'
    if excel:
        links_html.append("<a class='export-btn' href='/download?path={excel}' target='_blank'>{label}_excel.xlsx</a>".format(excel=html.escape(str(excel).replace('\\', '/')), label=html.escape(file_label)))
    if json_path:
        links_html.append("<a class='export-btn' href='/download?path={json}' target='_blank'>{label}_json.json</a>".format(json=html.escape(str(json_path).replace('\\', '/')), label=html.escape(file_label)))
    return "<div class='export-wrap'>%s</div>" % "\n".join(links_html)


def _build_status_message(result, error=None):
    if error:
        return "<div class='error'>%s</div>" % html.escape(str(error))
    if result and result.get("candidate_count", 0):
        return "<div class='export-wrap'><span class='chip'>Tarama tamamlandı</span></div>"
    return "<div class='error'>Amazon otomatik arama akışı engellendi. Sonuç gelmedi; lütfen başka kaynak veya URL deneyin veya farklı arama terimi kullanın.</div>"


def render_dashboard_page(result=None, error=None, form=None):
    saved = load_saved_filters()
    result = result or {}
    config = form or {
        "search_terms": saved.get('search_terms', ['portable blender']),
        "market": saved.get('market', 'com'),
        "min_roi": str(saved.get('min_roi', 25)),
        "max_risk": saved.get('max_risk', 'medium'),
        "min_sales": str(saved.get('min_sales', 300)),
        "max_fba": str(saved.get('max_fba', 12)),
        "categories": ','.join(saved.get('categories', ['Home', 'Kitchen', 'Office'])),
        "mode": saved.get('mode', 'bulk_search'),
        "asin": saved.get('asin', ''),
        "amazon_url": saved.get('amazon_url', ''),
        "exclude_hazmat": saved.get('exclude_hazmat', True),
        "prefer_no_amazon_seller": saved.get('prefer_no_amazon_seller', True),
    }
    if isinstance(config.get('search_terms'), str):
        config['search_terms'] = _clean_list(config['search_terms'])

    html_page = """
    <!doctype html>
    <html lang='tr'>
    <head>
      <meta charset='utf-8'>
      <title>Amazon AI Ajan Dashboard</title>
      <style>
        :root {{
          --bg: #f3f7ff;
          --panel: #ffffff;
          --line: #dfe7f3;
          --primary: #2457f5;
          --primary-soft: #e8efff;
          --text: #13233f;
          --muted: #64748b;
          --success: #0f9d58;
          --warning: #d97706;
          --danger: #dc2626;
        }}
        * {{ box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: var(--bg); margin: 0; color: var(--text); }}
        .container {{ max-width: 1280px; margin: 40px auto; padding: 24px; }}
        .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06); padding: 24px; margin-bottom: 24px; }}
        .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; flex-wrap: wrap; }}
        h1 {{ margin: 0; font-size: 2rem; }}
        .summary {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 16px; }}
        .chip {{ background: var(--primary-soft); color: var(--text); padding: 8px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
        .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }}
        .card {{ background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%); border: 1px solid var(--line); border-radius: 14px; padding: 18px; }}
        .card.muted {{ background: #f8fafc; }}
        .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
        .value {{ font-size: 2rem; font-weight: 700; margin: 8px 0 4px; }}
        .meta {{ color: var(--muted); font-size: 12px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
        .field {{ display: flex; flex-direction: column; gap: 6px; }}
        label {{ font-size: 12px; color: var(--muted); font-weight: 700; }}
        input, select {{ width: 100%; box-sizing: border-box; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--line); background: #fff; }}
        .checkbox-row {{ display: flex; align-items: center; gap: 8px; margin-top: 28px; }}
        input[type='checkbox'] {{ width: auto; }}
        button {{ background: var(--primary); color: white; border: none; padding: 12px 18px; border-radius: 10px; cursor: pointer; font-weight: 700; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ border-bottom: 1px solid var(--line); padding: 10px; text-align: left; vertical-align: top; }}
        th {{ background: #f8fbff; color: var(--text); }}
        a {{ color: var(--primary); text-decoration: none; }}
        .error {{ background: #fff1f2; color: #9f1239; border: 1px solid #fecdd3; padding: 12px 14px; border-radius: 10px; margin-top: 12px; }}
        .export-wrap {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }}
        .export-btn {{ display: inline-block; background: #eef2ff; color: #1d4ed8; border: 1px solid #c7d2fe; padding: 10px 14px; border-radius: 10px; font-weight: 700; }}
        .subhead {{ margin: 0 0 16px; }}
      </style>
    </head>
    <body>
      <div class='container'>
        <div class='panel'>
          <div class='topbar'>
            <div>
              <h1>Amazon AI Ajan Dashboard</h1>
              <div class='summary'>
                <span class='chip'>Arama terimleri: {search_terms}</span>
                <span class='chip'>Market: {market}</span>
                <span class='chip'>Sonuç: {candidate_count}</span>
              </div>
            </div>
            {export_links}
          </div>
        </div>

        <div class='panel'>
          <h2 class='subhead'>İşletme özeti</h2>
          <div class='kpis'>
            {summary_cards}
          </div>
        </div>

        <div class='panel'>
          <h2 class='subhead'>Tarama ve filtre ayarları</h2>
          <form method='POST'>
            <div class='grid'>
              <div class='field'>
                <label>Mod</label>
                <select name='mode'>
                  <option value='bulk_search' {mode_bulk}>Toplu arama</option>
                  <option value='single_asin' {mode_single}>Tek ASIN / ürün detay</option>
                </select>
              </div>
              <div class='field'>
                <label>Arama terimleri</label>
                <input name='search_terms' value='{search_terms_value}' placeholder='portable blender, desk organizer' />
              </div>
              <div class='field'>
                <label>Amazon linki</label>
                <input name='amazon_url' value='{amazon_url_value}' placeholder='https://www.amazon.com/dp/...' />
              </div>
              <div class='field'>
                <label>ASIN</label>
                <input name='asin' value='{asin_value}' placeholder='B0XXXX...' />
              </div>
              <div class='field'>
                <label>Market</label>
                <select name='market'>
                  <option value='com' {market_com}>US / Amazon.com</option>
                  <option value='de' {market_de}>DE / Amazon.de</option>
                </select>
              </div>
              <div class='field'>
                <label>Min ROI %</label>
                <input name='min_roi' value='{min_roi}' />
              </div>
              <div class='field'>
                <label>Max Risk</label>
                <select name='max_risk'>
                  <option value='low' {risk_low}>Low</option>
                  <option value='medium' {risk_medium}>Medium</option>
                  <option value='high' {risk_high}>High</option>
                </select>
              </div>
              <div class='field'>
                <label>Min aylık satış</label>
                <input name='min_sales' value='{min_sales}' />
              </div>
              <div class='field'>
                <label>Max FBA satıcı</label>
                <input name='max_fba' value='{max_fba}' />
              </div>
              <div class='field'>
                <label>Kategoriler</label>
                <input name='categories' value='{categories}' placeholder='Home,Kitchen,Office' />
              </div>
              <div class='field'>
                <label>Exclude hazmat</label>
                <div class='checkbox-row'>
                  <input type='checkbox' name='exclude_hazmat' {exclude_hazmat} />
                </div>
              </div>
              <div class='field'>
                <label>Amazon seller önceliği</label>
                <div class='checkbox-row'>
                  <input type='checkbox' name='prefer_no_amazon_seller' {prefer_no_amazon_seller} />
                </div>
              </div>
              <div class='field'>
                <label>Filtreyi kaydet</label>
                <div class='checkbox-row'>
                  <input type='checkbox' name='save_filter' {save_filter_checked} />
                </div>
              </div>
            </div>
            <div style='margin-top: 20px;'><button type='submit'>Ajanı çalıştır</button></div>
          </form>
          {error_html}
        </div>

        <div class='panel'>
          <h2 class='subhead'>Sonuç tablosu</h2>
          <table>
            <thead>
              <tr>
                <th>Ürün</th>
                <th>ASIN</th>
                <th>Market</th>
                <th>DE Fiyat</th>
                <th>ROI</th>
                <th>Skor</th>
                <th>Kaynak</th>
                <th>Amazon Link</th>
                <th>Doğrulanmış Başlık</th>
              </tr>
            </thead>
            <tbody>
              {candidate_rows}
            </tbody>
          </table>
        </div>
      </div>
    </body>
    </html>
    """

    selected_market = str(config.get("market") or "com")
    market_com = "selected" if selected_market == "com" else ""
    market_de = "selected" if selected_market == "de" else ""
    selected_mode = str(config.get("mode") or "bulk_search").lower()
    mode_bulk = "selected" if selected_mode == "bulk_search" else ""
    mode_single = "selected" if selected_mode == "single_asin" else ""
    selected_risk = str(config.get("max_risk") or "medium").lower()
    risk_low = "selected" if selected_risk == "low" else ""
    risk_medium = "selected" if selected_risk == "medium" else ""
    risk_high = "selected" if selected_risk == "high" else ""
    exclude_hazmat = "checked" if config.get("exclude_hazmat") else ""
    prefer_no_amazon_seller = "checked" if config.get("prefer_no_amazon_seller") else ""
    save_filter_checked = "checked" if config.get("save_filter") else ""

    error_html = _build_status_message(result, error)
    summary_cards = _build_summary_cards(result)
    export_links = _build_export_links(result)
    page = html_page.format(
        search_terms=", ".join(str(x) for x in _clean_list(config.get("search_terms", ["portable blender"]))),
        market=selected_market,
        candidate_count=result.get("candidate_count", 0),
        search_terms_value=html.escape(_as_text(config.get("search_terms", ["portable blender"]))),
        amazon_url_value=html.escape(_as_text(config.get("amazon_url", ""))),
        asin_value=html.escape(_as_text(config.get("asin", ""))),
        market_com=market_com,
        market_de=market_de,
        mode_bulk=mode_bulk,
        mode_single=mode_single,
        min_roi=html.escape(_as_text(config.get("min_roi", 25))),
        max_risk=html.escape(_as_text(config.get("max_risk", "medium"))),
        min_sales=html.escape(_as_text(config.get("min_sales", 300))),
        max_fba=html.escape(_as_text(config.get("max_fba", 12))),
        categories=html.escape(_as_text(config.get("categories", "Home,Kitchen,Office"))),
        exclude_hazmat=exclude_hazmat,
        prefer_no_amazon_seller=prefer_no_amazon_seller,
        save_filter_checked=save_filter_checked,
        risk_low=risk_low,
        risk_medium=risk_medium,
        risk_high=risk_high,
        error_html=error_html,
        candidate_rows=_render_candidate_rows(result.get("candidates", [])),
        summary_cards=summary_cards,
        export_links=export_links,
    )
    return page


class DashboardRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/download'):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            raw_path = urllib.parse.parse_qs(parsed.query).get('path', [''])[0]
            if not raw_path:
                self.send_response(400)
                self.end_headers()
                return
            file_path = Path(urllib.parse.unquote(raw_path))
            if not file_path.exists():
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{file_path.name}"')
            self.end_headers()
            with file_path.open('rb') as fh:
                self.wfile.write(fh.read())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(render_dashboard_page().encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw, keep_blank_values=True)
        form_data = {key: values[0] if values else "" for key, values in parsed.items()}

        try:
            config = build_dashboard_scan_config(form_data)
            if config.get('save_filter'):
                save_filter_config(config)
            result = run_dashboard_scan(config)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_dashboard_page(result=result, form={**form_data, **config}).encode("utf-8"))
        except Exception as exc:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_dashboard_page(error=str(exc), form=form_data).encode("utf-8"))

    def log_message(self, *args):
        return


def start_dashboard_server(host: str = "127.0.0.1", port: int = 8001):
    server = HTTPServer((host, port), DashboardRequestHandler)
    print(f"Amazon AI Dashboard is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    start_dashboard_server()
