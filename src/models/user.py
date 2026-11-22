
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:

    user_id: Optional[int] = None
    username: str = ""
    password_hash: str = field(default="", repr=False)
    full_name: str = ""
    is_active: bool = True
    created_at: Optional[str] = None

    def __post_init__(self):
        self.username = self.username.strip()
        self.full_name = self.full_name.strip()

        if not self.username:
            raise ValueError("Username cannot be empty.")

        if not self.full_name:
            raise ValueError("Full name cannot be empty.")

    @property
    def display_name(self) -> str:
        return self.full_name

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True
