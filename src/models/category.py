
from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    category_id: Optional[int] = None
    category_name: str = ""
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        self.category_name = self.category_name.strip()

        if not self.category_name:
            raise ValueError("Category name cannot be empty.")

        if self.parent_category_id is not None:
            if self.parent_category_id <= 0:
                raise ValueError("Parent category ID must be positive.")

        if self.is_active not in (0, 1):
            raise ValueError("is_active must be 0 or 1.")
