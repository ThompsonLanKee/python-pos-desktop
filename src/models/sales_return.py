
from dataclasses import dataclass
from typing import Optional


@dataclass
class SalesReturn:
    """Represents a physical product return against a sale."""

    return_number: str
    sale_id: int

    return_id: Optional[int] = None
    processed_by: Optional[int] = None
    return_status: str = "COMPLETED"
    total_refund_amount: int = 0
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    VALID_STATUSES = {"COMPLETED", "VOIDED"}

    def __post_init__(self):
        self.return_number = self.return_number.strip()
        self.return_status = self.return_status.strip().upper()

        if not self.return_number:
            raise ValueError("Return number is required.")

        if self.sale_id <= 0:
            raise ValueError("Sale ID must be positive.")

        if self.processed_by is not None and self.processed_by <= 0:
            raise ValueError("Processed-by user ID must be positive.")

        if (
            not isinstance(self.total_refund_amount, int)
            or isinstance(self.total_refund_amount, bool)
            or self.total_refund_amount < 0
        ):
            raise ValueError("Refund amount must be a non-negative integer.")

        if self.return_status not in self.VALID_STATUSES:
            raise ValueError("Invalid return status.")
