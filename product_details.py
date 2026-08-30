import re


def extract_product_details(html: str):
    title = ""
    image_url = ""
    price = 0.0

    title_match = re.search(r'<span[^>]*id=["\']productTitle["\'][^>]*>(.*?)</span>', html, re.DOTALL | re.IGNORECASE)
    if title_match:
        title = re.sub(r'<.*?>', '', title_match.group(1))
        title = ' '.join(title.split())

    if not title:
        title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        if title_match:
            title = re.sub(r'<.*?>', '', title_match.group(1))
            title = title.replace("- Amazon", "").strip()

    image_match = re.search(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', html, re.DOTALL | re.IGNORECASE)
    if image_match:
        image_url = image_match.group(1)

    price_whole_match = re.search(r'<span[^>]*class=["\']a-price-whole["\'][^>]*>([0-9,]+)', html, re.DOTALL | re.IGNORECASE)
    price_fraction_match = re.search(r'<span[^>]*class=["\']a-price-fraction["\'][^>]*>([0-9]+)', html, re.DOTALL | re.IGNORECASE)

    if price_whole_match:
        whole = price_whole_match.group(1).replace(',', '')
        fraction = price_fraction_match.group(1) if price_fraction_match else '00'
        try:
            price = float(f"{whole}.{fraction}")
        except ValueError:
            price = float(whole)

    return {
        "title": title,
        "image_url": image_url,
        "price": round(price, 2),
    }
