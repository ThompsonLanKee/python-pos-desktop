
from dataclasses import dataclass
from typing import Optional


@dataclass
class Permission:

    permission_id: Optional[int] = None
    permission_code: str = ""
    description: Optional[str] = None

    def __post_init__(self):
        self.permission_code = self.permission_code.strip().upper()

        if not self.permission_code:
            raise ValueError("Permission code cannot be empty.")

    def update_description(self, description: str):
        self.description = description.strip()
