
from dataclasses import dataclass
from typing import Optional


@dataclass
class Refund:
    """Represents money refunded against an original payment."""

    payment_id: int
    sale_id: int
    amount: int

    refund_id: Optional[int] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):

        if (
            not isinstance(self.payment_id, int)
            or isinstance(self.payment_id, bool)
            or self.payment_id <= 0
        ):
            raise ValueError("Payment ID must be a positive integer.")

        if (
            not isinstance(self.sale_id, int)
            or isinstance(self.sale_id, bool)
            or self.sale_id <= 0
        ):
            raise ValueError("Sale ID must be a positive integer.")

        if (
            not isinstance(self.amount, int)
            or isinstance(self.amount, bool)
            or self.amount <= 0
        ):
            raise ValueError("Refund amount must be a positive integer.")

        if self.reference_number is not None:
            self.reference_number = (
                self.reference_number.strip() or None
            )
