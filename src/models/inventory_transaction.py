
from dataclasses import dataclass
from typing import Optional , ClassVar


@dataclass
class InventoryTransaction:
    """Represents one inventory stock movement."""

    variant_id: int
    transaction_type: str
    quantity_change: int
    quantity_after: int

    transaction_id: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    VALID_TYPES: ClassVar[set[str]] = {
    "OPENING",
    "PURCHASE",
    "SALE",
    "SALE_RETURN",
    "PURCHASE_RETURN",
    "ADJUSTMENT_IN",
    "ADJUSTMENT_OUT",
    "DAMAGE",
}

    def __post_init__(self):
        self.transaction_type = self.transaction_type.strip().upper()

        if self.variant_id <= 0:
            raise ValueError("Variant ID must be positive.")

        if self.transaction_type not in self.VALID_TYPES:
            raise ValueError("Invalid inventory transaction type.")

        if self.quantity_change == 0:
            raise ValueError("Quantity change cannot be zero.")

        if self.quantity_after < 0:
            raise ValueError("Quantity after cannot be negative.")

        if self.reference_id is not None and self.reference_id <= 0:
            raise ValueError("Reference ID must be positive.")

        if self.reference_type is not None:
            self.reference_type = self.reference_type.strip() or None
