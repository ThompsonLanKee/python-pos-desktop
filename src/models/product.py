from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:

    product_id: Optional[int] = None
    product_name: str = ""
    description: Optional[str] = None
    category_id: int = 0
    brand: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    image_path: Optional[str] = None

    def __post_init__(self):
        self.product_name = self.product_name.strip()

        if not self.product_name:
            raise ValueError("Product name cannot be empty.")

        if self.category_id <= 0:
            raise ValueError("A valid category is required.")

        if self.description is not None:
            self.description = self.description.strip() or None

        if self.brand is not None:
            self.brand = self.brand.strip() or None

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True