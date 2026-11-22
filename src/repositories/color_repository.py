
from typing import Optional

from src.models import Color
from src.repositories.base_repository import BaseRepository


class ColorRepository(BaseRepository):
    """Handles product color database operations."""

    def create(self, color: Color) -> int:
        query = """
            INSERT INTO colors (
                color_name,
                hex_code,
                is_active
            )
            VALUES (?, ?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    color.color_name,
                    color.hex_code,
                    color.is_active
                )
            )

            return cursor.lastrowid

    def get_by_id(self, color_id: int) -> Optional[Color]:

        query = """
            SELECT *
            FROM colors
            WHERE color_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (color_id,)
            ).fetchone()

            return Color(**dict(row)) if row else None

    def get_by_name(self, color_name: str) -> Optional[Color]:

        query = """
            SELECT *
            FROM colors
            WHERE color_name = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (color_name.strip(),)
            ).fetchone()

            return Color(**dict(row)) if row else None

    def get_all(self) -> list[Color]:

        query = """
            SELECT *
            FROM colors
            ORDER BY color_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Color(**dict(row))
                for row in rows
            ]

    def get_active(self) -> list[Color]:

        query = """
            SELECT *
            FROM colors
            WHERE is_active = 1
            ORDER BY color_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Color(**dict(row))
                for row in rows
            ]

    def update(self, color: Color) -> bool:

        if color.color_id is None:
            raise ValueError("Color ID is required.")

        query = """
            UPDATE colors
            SET color_name = ?,
                hex_code = ?
            WHERE color_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    color.color_name,
                    color.hex_code,
                    color.color_id
                )
            )

            return cursor.rowcount > 0

    def set_active(
        self,
        color_id: int,
        is_active: bool
    ) -> bool:

        query = """
            UPDATE colors
            SET is_active = ?
            WHERE color_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (int(is_active), color_id)
            )

            return cursor.rowcount > 0
