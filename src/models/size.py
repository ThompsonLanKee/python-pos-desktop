from dataclasses import dataclass
from typing import Optional


@dataclass
class Size:

    size_id: Optional[int] = None
    size_name: str = ""
    sort_order: int = 0
    is_active: bool = True

    def __post_init__(self):
        self.size_name = self.size_name.strip()

        if not self.size_name:
            raise ValueError("Size name cannot be empty.")

        if self.sort_order < 0:
            raise ValueError("Size sort order cannot be negative.")
