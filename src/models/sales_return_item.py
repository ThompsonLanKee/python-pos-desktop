
from dataclasses import dataclass
from typing import Optional


@dataclass
class SalesReturnItem:
    """Represents a returned quantity from an original sale item."""

    return_id: int
    sale_item_id: int
    variant_id: int
    quantity: int
    unit_refund_amount: int
    line_refund_amount: int

    return_item_id: Optional[int] = None
    restock: int = 1
    condition: str = "GOOD"
    notes: Optional[str] = None
    created_at: Optional[str] = None

    VALID_CONDITIONS = {"GOOD", "DAMAGED", "DEFECTIVE"}

    def __post_init__(self):
        self.condition = self.condition.strip().upper()

        for name, value in (
            ("return_id", self.return_id),
            ("sale_item_id", self.sale_item_id),
            ("variant_id", self.variant_id),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(f"{name} must be a positive integer.")

        if (
            not isinstance(self.quantity, int)
            or isinstance(self.quantity, bool)
            or self.quantity <= 0
        ):
            raise ValueError("Quantity must be a positive integer.")

        for name, value in (
            ("unit_refund_amount", self.unit_refund_amount),
            ("line_refund_amount", self.line_refund_amount),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer.")

            if self.line_refund_amount > (
                 self.quantity * self.unit_refund_amount
            ):
                 raise ValueError("Line refund cannot exceed the original gross amount.")

        if self.restock not in (0, 1):
            raise ValueError("Restock must be 0 or 1.")

        if self.condition not in self.VALID_CONDITIONS:
            raise ValueError("Invalid returned item condition.")

        if self.restock == 1 and self.condition != "GOOD":
            raise ValueError(
                "Only goods in GOOD condition can be restocked."
            )
