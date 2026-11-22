
import sqlite3
from typing import Optional

from src.models import Product
from src.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    """
    Handles database operations for products.
    """

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        product: Product,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a new product."""

        query = """
            INSERT INTO products (
                product_name,
                description,
                category_id,
                brand,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    product.product_name,
                    product.description,
                    product.category_id,
                    product.brand,
                    product.is_active
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_by_id(
        self,
        product_id: int
    ) -> Optional[Product]:
        """Retrieve a product by ID."""

        query = """
            SELECT *
            FROM products
            WHERE product_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (product_id,)
            ).fetchone()

            return Product(**dict(row)) if row else None

    def get_all(self) -> list[Product]:
        """Retrieve all products."""

        query = """
            SELECT *
            FROM products
            ORDER BY product_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Product(**dict(row))
                for row in rows
            ]

    def get_active(self) -> list[Product]:
        """Retrieve active products."""

        query = """
            SELECT *
            FROM products
            WHERE is_active = 1
            ORDER BY product_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Product(**dict(row))
                for row in rows
            ]

    def get_by_category(
        self,
        category_id: int
    ) -> list[Product]:
        """Retrieve products belonging to a category."""

        query = """
            SELECT *
            FROM products
            WHERE category_id = ?
            ORDER BY product_name
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (category_id,)
            ).fetchall()

            return [
                Product(**dict(row))
                for row in rows
            ]

    def search(
        self,
        keyword: str
    ) -> list[Product]:
        """Search products by name or brand."""

        query = """
            SELECT *
            FROM products
            WHERE product_name LIKE ?
               OR brand LIKE ?
            ORDER BY product_name
        """

        search_term = f"%{keyword.strip()}%"

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (search_term, search_term)
            ).fetchall()

            return [
                Product(**dict(row))
                for row in rows
            ]

    # ==========================================
    # UPDATE
    # ==========================================

    def update(
        self,
        product: Product,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update product information."""

        if product.product_id is None:
            raise ValueError("Product ID is required.")

        query = """
            UPDATE products
            SET product_name = ?,
                description = ?,
                category_id = ?,
                brand = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    product.product_name,
                    product.description,
                    product.category_id,
                    product.brand,
                    product.product_id
                )
            )

            return cursor.rowcount > 0

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    def set_active(
        self,
        product_id: int,
        is_active: bool,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Activate or deactivate a product."""

        query = """
            UPDATE products
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (int(is_active), product_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists(self, product_id: int) -> bool:
        """Check whether a product exists."""

        query = """
            SELECT 1
            FROM products
            WHERE product_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (product_id,)
            ).fetchone()

            return row is not None

    def get_category_id(
        self,
        product_id: int
    ) -> Optional[int]:
        """Retrieve the category ID of a product."""

        query = """
            SELECT category_id
            FROM products
            WHERE product_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (product_id,)
            ).fetchone()

            return row["category_id"] if row else None
