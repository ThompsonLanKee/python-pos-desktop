
from dataclasses import dataclass
from typing import Optional


@dataclass
class Refund:
    """Represents money refunded against an original payment and sale return."""

    payment_id: int
    sale_id: int
    amount: int

    refund_id: Optional[int] = None
    return_id: Optional[int] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        self._validate_positive_id(self.payment_id, "Payment ID")
        self._validate_positive_id(self.sale_id, "Sale ID")

        if self.return_id is not None:
            self._validate_positive_id(self.return_id, "Return ID")

        if (
            not isinstance(self.amount, int)
            or isinstance(self.amount, bool)
            or self.amount <= 0
        ):
            raise ValueError("Refund amount must be a positive integer.")

        if self.reference_number is not None:
            self.reference_number = self.reference_number.strip() or None

    @staticmethod
    def _validate_positive_id(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(f"{field_name} must be a positive integer.")
