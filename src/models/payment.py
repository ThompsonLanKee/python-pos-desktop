
from dataclasses import dataclass
from typing import Optional


@dataclass
class Payment:
    """Represents a payment against a POS sale."""

    sale_id: int
    payment_method: str
    amount: int

    payment_id: Optional[int] = None
    payment_status: str = "COMPLETED"
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    VALID_METHODS = {
        "CASH",
        "CARD",
        "MOBILE",
        "BANK_TRANSFER",
        "OTHER",
    }

    VALID_STATUSES = {
        "COMPLETED",
        "FAILED",
        "REFUNDED",
    }

    def __post_init__(self):
        self.payment_method = self.payment_method.strip().upper()
        self.payment_status = self.payment_status.strip().upper()

        if self.sale_id <= 0:
            raise ValueError("Sale ID must be positive.")

        if (
            not isinstance(self.amount, int)
            or isinstance(self.amount, bool)
            or self.amount <= 0
        ):
            raise ValueError("Payment amount must be positive.")

        if self.payment_method not in self.VALID_METHODS:
            raise ValueError("Invalid payment method.")

        if self.payment_status not in self.VALID_STATUSES:
            raise ValueError("Invalid payment status.")

        if self.reference_number is not None:
            self.reference_number = (
                self.reference_number.strip() or None
            )
