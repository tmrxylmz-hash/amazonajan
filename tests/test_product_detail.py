from product_details import extract_product_details


def test_extract_product_details_parses_amazon_like_html():
    html = """
    <html>
      <head>
        <title>Portable Blender - Amazon</title>
      </head>
      <body>
        <img src="https://images.example.com/blender.jpg" />
        <span id="productTitle">Portable Blender</span>
        <span class="a-price-whole">29</span>
        <span class="a-price-fraction">99</span>
      </body>
    </html>
    """

    details = extract_product_details(html)

    assert details["title"] == "Portable Blender"
    assert details["price"] == 29.99
    assert details["image_url"].endswith("blender.jpg")
