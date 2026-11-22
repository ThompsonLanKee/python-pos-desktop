
from typing import Optional

from src.models import Category
from src.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):
    """
    Handles database operations for product categories.
    """

    # ==========================================
    # CREATE
    # ==========================================

    def create(self, category: Category) -> int:
        """Create a new category."""

        query = """
            INSERT INTO categories (
                category_name,
                description,
                parent_category_id,
                is_active
            )
            VALUES (?, ?, ?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    category.category_name,
                    category.description,
                    category.parent_category_id,
                    category.is_active
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_by_id(
        self,
        category_id: int
    ) -> Optional[Category]:
        """Retrieve a category by ID."""

        query = """
            SELECT *
            FROM categories
            WHERE category_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (category_id,)
            ).fetchone()

            return Category(**dict(row)) if row else None

    def get_by_name(
        self,
        category_name: str
    ) -> Optional[Category]:
        """Retrieve a category by name."""

        query = """
            SELECT *
            FROM categories
            WHERE category_name = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (category_name.strip(),)
            ).fetchone()

            return Category(**dict(row)) if row else None

    def get_all(self) -> list[Category]:
        """Retrieve all categories."""

        query = """
            SELECT *
            FROM categories
            ORDER BY category_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Category(**dict(row))
                for row in rows
            ]

    def get_active(self) -> list[Category]:
        """Retrieve active categories."""

        query = """
            SELECT *
            FROM categories
            WHERE is_active = 1
            ORDER BY category_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Category(**dict(row))
                for row in rows
            ]

    def get_children(
        self,
        parent_category_id: int
    ) -> list[Category]:
        """Retrieve direct child categories."""

        query = """
            SELECT *
            FROM categories
            WHERE parent_category_id = ?
            ORDER BY category_name
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (parent_category_id,)
            ).fetchall()

            return [
                Category(**dict(row))
                for row in rows
            ]

    # ==========================================
    # UPDATE
    # ==========================================

    def update(self, category: Category) -> bool:
        """Update category information."""

        if category.category_id is None:
            raise ValueError("Category ID is required.")

        query = """
            UPDATE categories
            SET category_name = ?,
                description = ?,
                parent_category_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    category.category_name,
                    category.description,
                    category.parent_category_id,
                    category.category_id
                )
            )

            return cursor.rowcount > 0

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    def set_active(
        self,
        category_id: int,
        is_active: bool
    ) -> bool:
        """Activate or deactivate a category."""

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

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists(self, category_id: int) -> bool:
        """Check whether a category exists."""

        query = """
            SELECT 1
            FROM categories
            WHERE category_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (category_id,)
            ).fetchone()

            return row is not None

    def has_products(self, category_id: int) -> bool:
        """Check whether a category contains products."""

        query = """
            SELECT 1
            FROM products
            WHERE category_id = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (category_id,)
            ).fetchone()

            return row is not None
