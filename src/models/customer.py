
from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """Represents a POS customer."""

    customer_name: str
    customer_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        self.customer_name = self.customer_name.strip()

        if not self.customer_name:
            raise ValueError("Customer name is required.")

        if self.phone is not None:
            self.phone = self.phone.strip() or None

        if self.email is not None:
            self.email = self.email.strip() or None

        if self.address is not None:
            self.address = self.address.strip() or None

        if self.is_active not in (0, 1):
            raise ValueError("is_active must be 0 or 1.")
