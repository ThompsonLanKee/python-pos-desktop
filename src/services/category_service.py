
import sqlite3
from contextlib import closing

from src.core.database import Database


class CategoryService:
    """Handles category management and validation."""

    def __init__(self, database: Database):
        self.database = database

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_all_categories(self) -> list[dict]:
        """Return all categories, including inactive ones."""

        with closing(self.database.connect()) as connection:
            rows = connection.execute("""
                SELECT
                    c.category_id,
                    c.category_name,
                    c.description,
                    c.parent_category_id,
                    p.category_name AS parent_category_name,
                    c.is_active,
                    c.created_at,
                    c.updated_at
                FROM categories c
                LEFT JOIN categories p
                    ON c.parent_category_id = p.category_id
                ORDER BY c.category_name COLLATE NOCASE
            """).fetchall()

            return [dict(row) for row in rows]

    def get_active_categories(self) -> list[dict]:
        """Return active categories for product forms."""

        with closing(self.database.connect()) as connection:
            rows = connection.execute("""
                SELECT
                    category_id,
                    category_name,
                    description,
                    parent_category_id
                FROM categories
                WHERE is_active = 1
                ORDER BY category_name COLLATE NOCASE
            """).fetchall()

            return [dict(row) for row in rows]

    # ==========================================
    # VALIDATION
    # ==========================================

    @staticmethod
    def _validate_category_name(category_name: str) -> str:
        if not isinstance(category_name, str):
            raise TypeError("Category name must be text.")

        category_name = category_name.strip()

        if not category_name:
            raise ValueError("Category name is required.")

        if len(category_name) > 100:
            raise ValueError(
                "Category name cannot exceed 100 characters."
            )

        return category_name

    @staticmethod
    def _validate_description(description: str | None) -> str | None:
        if description is None:
            return None

        if not isinstance(description, str):
            raise TypeError("Description must be text.")

        description = description.strip()
        return description or None

    def _validate_parent(
        self,
        connection,
        parent_category_id: int | None,
        category_id: int | None = None,
    ):
        if parent_category_id is None:
            return

        if (
            not isinstance(parent_category_id, int)
            or isinstance(parent_category_id, bool)
            or parent_category_id <= 0
        ):
            raise ValueError("Invalid parent category.")

        if category_id == parent_category_id:
            raise ValueError(
                "A category cannot be its own parent."
            )

        parent = connection.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = ?
              AND is_active = 1
        """, (parent_category_id,)).fetchone()

        if parent is None:
            raise ValueError(
                "Parent category does not exist or is inactive."
            )

        # Prevent circular category relationships.
        current_parent_id = parent_category_id

        while current_parent_id is not None:
            if current_parent_id == category_id:
                raise ValueError(
                    "This parent would create a category hierarchy cycle."
                )

            row = connection.execute("""
                SELECT parent_category_id
                FROM categories
                WHERE category_id = ?
            """, (current_parent_id,)).fetchone()

            current_parent_id = (
                row["parent_category_id"] if row else None
            )

    # ==========================================
    # CREATE
    # ==========================================

    def create_category(
        self,
        category_name: str,
        description: str | None = None,
        parent_category_id: int | None = None,
    ) -> int:

        category_name = self._validate_category_name(category_name)
        description = self._validate_description(description)

        try:
            with self.database.transaction() as connection:
                self._validate_parent(
                    connection,
                    parent_category_id
                )

                cursor = connection.execute("""
                    INSERT INTO categories (
                        category_name,
                        description,
                        parent_category_id
                    )
                    VALUES (?, ?, ?)
                """, (
                    category_name,
                    description,
                    parent_category_id
                ))

                return cursor.lastrowid

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Category name already exists or violates a database constraint."
            ) from error

    # ==========================================
    # UPDATE
    # ==========================================

    def update_category(
        self,
        category_id: int,
        category_name: str,
        description: str | None = None,
        parent_category_id: int | None = None,
    ) -> bool:

        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id <= 0
        ):
            raise ValueError("Invalid category ID.")

        category_name = self._validate_category_name(category_name)
        description = self._validate_description(description)

        try:
            with self.database.transaction() as connection:

                existing = connection.execute("""
                    SELECT category_id
                    FROM categories
                    WHERE category_id = ?
                """, (category_id,)).fetchone()

                if existing is None:
                    raise ValueError("Category was not found.")

                self._validate_parent(
                    connection,
                    parent_category_id,
                    category_id
                )

                cursor = connection.execute("""
                    UPDATE categories
                    SET
                        category_name = ?,
                        description = ?,
                        parent_category_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE category_id = ?
                """, (
                    category_name,
                    description,
                    parent_category_id,
                    category_id
                ))

                return cursor.rowcount > 0

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Category name already exists or violates a database constraint."
            ) from error

    # ==========================================
    # ACTIVATE / DEACTIVATE
    # ==========================================

    def set_category_active(
        self,
        category_id: int,
        is_active: bool,
    ) -> bool:

        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id <= 0
        ):
            raise ValueError("Invalid category ID.")

        if not isinstance(is_active, bool):
            raise TypeError("is_active must be True or False.")

        with self.database.transaction() as connection:

            category = connection.execute("""
                SELECT category_id
                FROM categories
                WHERE category_id = ?
            """, (category_id,)).fetchone()

            if category is None:
                raise ValueError("Category was not found.")

            if not is_active:
                active_children = connection.execute("""
                    SELECT COUNT(*)
                    FROM categories
                    WHERE parent_category_id = ?
                      AND is_active = 1
                """, (category_id,)).fetchone()[0]

                if active_children:
                    raise ValueError(
                        "Deactivate or reassign active subcategories first."
                    )

                assigned_products = connection.execute("""
                    SELECT COUNT(*)
                    FROM products
                    WHERE category_id = ?
                      AND is_active = 1
                """, (category_id,)).fetchone()[0]

                if assigned_products:
                    raise ValueError(
                        "Move or deactivate the active products in this category first."
                    )

            cursor = connection.execute("""
                UPDATE categories
                SET
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE category_id = ?
            """, (1 if is_active else 0, category_id))

            return cursor.rowcount > 0
