
from dataclasses import dataclass
from typing import Optional


@dataclass
class Role:

    role_id: Optional[int] = None
    role_name: str = ""
    description: Optional[str] = None

    def __post_init__(self):
        self.role_name = self.role_name.strip()

        if not self.role_name:
            raise ValueError("Role name cannot be empty.")

    def rename(self, new_name: str):
        new_name = new_name.strip()

        if not new_name:
            raise ValueError("Role name cannot be empty.")

        self.role_name = new_name

    def update_description(self, description: str):
        self.description = description.strip()
