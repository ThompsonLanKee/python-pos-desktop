
from dataclasses import dataclass
from typing import Optional


@dataclass
class SaleItem:
    """Represents one product variant sold in a sale."""

    sale_id: int
    variant_id: int
    product_name: str
    sku: str
    quantity: int
    unit_cost: int
    unit_price: int
    discount_amount: int
    line_total: int

    sale_item_id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        self.product_name = self.product_name.strip()
        self.sku = self.sku.strip().upper()

        if self.sale_id <= 0:
            raise ValueError("Sale ID must be positive.")

        if self.variant_id <= 0:
            raise ValueError("Variant ID must be positive.")

        if not self.product_name:
            raise ValueError("Product name is required.")

        if not self.sku:
            raise ValueError("SKU is required.")

        if (
            not isinstance(self.quantity, int)
            or isinstance(self.quantity, bool)
            or self.quantity <= 0
        ):
            raise ValueError("Quantity must be a positive integer.")

        for name, value in (
            ("unit_cost", self.unit_cost),
            ("unit_price", self.unit_price),
            ("discount_amount", self.discount_amount),
            ("line_total", self.line_total),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{name} must be a non-negative integer."
                )

        gross_total = self.quantity * self.unit_price

        if self.discount_amount > gross_total:
            raise ValueError(
                "Line discount cannot exceed the gross line total."
            )

        if self.line_total != gross_total - self.discount_amount:
            raise ValueError(
                "Line total calculation is incorrect."
            )
