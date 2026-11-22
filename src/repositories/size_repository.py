
from typing import Optional

from src.models import Size
from src.repositories.base_repository import BaseRepository


class SizeRepository(BaseRepository):
    """Handles product size database operations."""

    def create(self, size: Size) -> int:

        query = """
            INSERT INTO sizes (
                size_name,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    size.size_name,
                    size.sort_order,
                    size.is_active
                )
            )

            return cursor.lastrowid

    def get_by_id(self, size_id: int) -> Optional[Size]:

        query = """
            SELECT *
            FROM sizes
            WHERE size_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (size_id,)
            ).fetchone()

            return Size(**dict(row)) if row else None

    def get_by_name(self, size_name: str) -> Optional[Size]:

        query = """
            SELECT *
            FROM sizes
            WHERE size_name = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (size_name.strip(),)
            ).fetchone()

            return Size(**dict(row)) if row else None

    def get_all(self) -> list[Size]:

        query = """
            SELECT *
            FROM sizes
            ORDER BY sort_order, size_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Size(**dict(row))
                for row in rows
            ]

    def get_active(self) -> list[Size]:

        query = """
            SELECT *
            FROM sizes
            WHERE is_active = 1
            ORDER BY sort_order, size_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Size(**dict(row))
                for row in rows
            ]

    def update(self, size: Size) -> bool:

        if size.size_id is None:
            raise ValueError("Size ID is required.")

        query = """
            UPDATE sizes
            SET size_name = ?,
                sort_order = ?
            WHERE size_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    size.size_name,
                    size.sort_order,
                    size.size_id
                )
            )

            return cursor.rowcount > 0

    def set_active(
        self,
        size_id: int,
        is_active: bool
    ) -> bool:

        query = """
            UPDATE sizes
            SET is_active = ?
            WHERE size_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (int(is_active), size_id)
            )

            return cursor.rowcount > 0
