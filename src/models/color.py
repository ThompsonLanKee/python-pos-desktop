from dataclasses import dataclass
from typing import Optional


@dataclass
class Color:

    color_id: Optional[int] = None
    color_name: str = ""
    hex_code: Optional[str] = None
    is_active: bool = True

    def __post_init__(self):
        self.color_name = self.color_name.strip()

        if not self.color_name:
            raise ValueError("Color name cannot be empty.")

        if self.hex_code is not None:
            self.hex_code = self.hex_code.strip().upper() or None
