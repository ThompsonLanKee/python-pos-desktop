
from dataclasses import dataclass
from typing import Optional


@dataclass
class Sale:
    """Represents a POS sale header."""

    sale_number: str
    subtotal: int
    discount_amount: int
    tax_amount: int
    total_amount: int

    sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    cashier_user_id: Optional[int] = None
    sale_status: str = "COMPLETED"
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    VALID_STATUSES = {
        "COMPLETED",
        "VOIDED",
        "REFUNDED",
    }

    def __post_init__(self):
        self.sale_number = self.sale_number.strip()
        self.sale_status = self.sale_status.strip().upper()

        if not self.sale_number:
            raise ValueError("Sale number is required.")

        amounts = {
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
        }

        for name, value in amounts.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{name} must be a non-negative integer."
                )

        if self.discount_amount > self.subtotal:
            raise ValueError(
                "Discount cannot exceed subtotal."
            )

        expected_total = (
            self.subtotal
            - self.discount_amount
            + self.tax_amount
        )

        if self.total_amount != expected_total:
            raise ValueError(
                "Total must equal subtotal - discount + tax."
            )

        if self.sale_status not in self.VALID_STATUSES:
            raise ValueError("Invalid sale status.")

        if self.customer_id is not None and self.customer_id <= 0:
            raise ValueError("Customer ID must be positive.")

        if (
            self.cashier_user_id is not None
            and self.cashier_user_id <= 0
        ):
            raise ValueError("Cashier user ID must be positive.")
