from config import SEARCH_CRITERIA


def generate_ai_summary(candidate, criteria=None) -> str:
    if criteria is None:
        criteria = SEARCH_CRITERIA

    positives = []
    negatives = []

    if candidate.estimated_roi >= criteria.get("min_roi_percent", 0):
        positives.append("ROI hedef eşik üzerinde.")
    if candidate.monthly_sales >= criteria.get("min_monthly_sales", 0):
        positives.append("aylık satış hacmi güçlü.")
    if candidate.fba_sellers <= criteria.get("max_fba_sellers", 99):
        positives.append("rekabet seviyesi yönetilebilir.")
    if candidate.risk_level.lower() in {"low", "medium"}:
        positives.append("risk seviyesi kabul edilebilir.")
    if not candidate.amazon_seller:
        positives.append("Amazon kendi satıcısı değil.")
    if candidate.category in criteria.get("product_categories", []):
        positives.append("hedef kategoriyle uyumlu.")

    if candidate.amazon_seller:
        negatives.append("Amazon satıcısı olması risk yaratıyor.")
    if candidate.fba_sellers > criteria.get("max_fba_sellers", 99):
        negatives.append("FBA rekabeti yüksek.")
    if candidate.risk_level.lower() == "high":
        negatives.append("risk seviyesi yüksek.")
    if candidate.estimated_profit <= 0:
        negatives.append("netic kâr sıfırın altında.")

    summary = ", ".join(positives) if positives else "kriterler açısından zayıf görünüm."
    if negatives:
        summary += ". Dikkat: " + "; ".join(negatives)

    if candidate.estimated_roi >= 45:
        summary += " Bu aday güçlü fırsat olma potansiyeline sahip."
    elif candidate.estimated_roi >= 25:
        summary += " Bu aday izlenmeye değer bir fırsat."
    else:
        summary += " Bu aday daha fazla inceleme gerektiriyor."

    return summary
