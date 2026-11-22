from typing import Optional

from src.models import Category
from src.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):

    def create(self, category: Category) -> int:
        query = """
            INSERT INTO categories (
                category_name,
                description,
                is_active
            )
            VALUES (?, ?, ?)
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    category.category_name,
                    category.description,
                    int(category.is_active)
                )
            )
            return cursor.lastrowid

    def get_by_id(self, category_id: int) -> Optional[Category]:
        query = """
            SELECT *
            FROM categories
            WHERE category_id = ?
        """

        with self.connection() as connection:
            row = connection.execute(query, (category_id,)).fetchone()
            return self._to_category(row) if row else None

    def get_by_name(self, category_name: str) -> Optional[Category]:
        query = """
            SELECT *
            FROM categories
            WHERE category_name COLLATE NOCASE = ?
        """

        with self.connection() as connection:
            row = connection.execute(
                query,
                (category_name.strip(),)
            ).fetchone()
            return self._to_category(row) if row else None

    def get_all(self, active_only: bool = False) -> list[Category]:
        query = """
            SELECT *
            FROM categories
        """

        parameters = ()

        if active_only:
            query += " WHERE is_active = 1"

        query += " ORDER BY category_name COLLATE NOCASE"

        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
            return [self._to_category(row) for row in rows]

    def update(self, category: Category) -> bool:
        if category.category_id is None:
            raise ValueError("Category ID is required.")

        query = """
            UPDATE categories
            SET category_name = ?,
                description = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = ?
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    category.category_name,
                    category.description,
                    int(category.is_active),
                    category.category_id
                )
            )
            return cursor.rowcount > 0

    def set_active(self, category_id: int, is_active: bool) -> bool:
        query = """
            UPDATE categories
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = ?
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (int(is_active), category_id)
            )
            return cursor.rowcount > 0

    def delete(self, category_id: int) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM categories WHERE category_id = ?",
                (category_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def _to_category(row) -> Category:
        data = dict(row)
        data["is_active"] = bool(data["is_active"])
        return Category(**data)