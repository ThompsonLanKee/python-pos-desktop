from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:

    category_id: Optional[int] = None
    category_name: str = ""
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        self.category_name = self.category_name.strip()

        if not self.category_name:
            raise ValueError("Category name cannot be empty.")

        if self.description is not None:
            self.description = self.description.strip() or None

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True