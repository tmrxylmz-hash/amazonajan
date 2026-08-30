from dataclasses import dataclass


@dataclass
class ProductCandidate:
    product_name: str
    asin: str
    us_price: float
    de_price: float
    monthly_sales: int
    fba_sellers: int
    amazon_seller: bool
    estimated_profit: float
    estimated_roi: float
    risk_level: str
    category: str
    image_url: str | None = None

    def score_ready(self) -> bool:
        return self.estimated_roi > 0 and self.monthly_sales > 0
