from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductVariant:

    variant_id: Optional[int] = None
    product_id: int = 0
    sku: Optional[str] = None
    barcode: Optional[str] = None
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    cost_price: float = 0
    selling_price: float = 0
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.product_id <= 0:
            raise ValueError("A valid product is required.")

        self.sku = self._clean_code(self.sku)
        self.barcode = self._clean_code(self.barcode)

        if self.cost_price < 0:
            raise ValueError("Cost price cannot be negative.")

        if self.selling_price < 0:
            raise ValueError("Selling price cannot be negative.")

    @staticmethod
    def _clean_code(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()
        return value or None

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True
