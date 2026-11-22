
from typing import Optional

from src.models import ProductVariant
from src.repositories.base_repository import BaseRepository


class ProductVariantRepository(BaseRepository):
    """Handles product variant database operations."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(self, variant: ProductVariant) -> int:

        query = """
            INSERT INTO product_variants (
                product_id,
                color_id,
                size_id,
                sku,
                barcode,
                cost_price,
                selling_price,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    variant.product_id,
                    variant.color_id,
                    variant.size_id,
                    variant.sku,
                    variant.barcode,
                    variant.cost_price,
                    variant.selling_price,
                    variant.is_active
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_by_id(
        self,
        variant_id: int
    ) -> Optional[ProductVariant]:

        query = """
            SELECT *
            FROM product_variants
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (variant_id,)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    def get_by_sku(
        self,
        sku: str
    ) -> Optional[ProductVariant]:

        query = """
            SELECT *
            FROM product_variants
            WHERE sku = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (sku.strip(),)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    def get_by_barcode(
        self,
        barcode: str
    ) -> Optional[ProductVariant]:

        query = """
            SELECT *
            FROM product_variants
            WHERE barcode = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (barcode.strip(),)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    def get_by_product(
        self,
        product_id: int
    ) -> list[ProductVariant]:

        query = """
            SELECT *
            FROM product_variants
            WHERE product_id = ?
            ORDER BY variant_id
        """

        with self.connection() as connection:

            rows = connection.execute(
                query, (product_id,)
            ).fetchall()

            return [
                ProductVariant(**dict(row))
                for row in rows
            ]

    def get_all(self) -> list[ProductVariant]:

        query = """
            SELECT *
            FROM product_variants
            ORDER BY variant_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                ProductVariant(**dict(row))
                for row in rows
            ]

    # ==========================================
    # UPDATE
    # ==========================================

    def update(self, variant: ProductVariant) -> bool:

        if variant.variant_id is None:
            raise ValueError("Variant ID is required.")

        query = """
            UPDATE product_variants
            SET color_id = ?,
                size_id = ?,
                sku = ?,
                barcode = ?,
                cost_price = ?,
                selling_price = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    variant.color_id,
                    variant.size_id,
                    variant.sku,
                    variant.barcode,
                    variant.cost_price,
                    variant.selling_price,
                    variant.variant_id
                )
            )

            return cursor.rowcount > 0

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    def set_active(
        self,
        variant_id: int,
        is_active: bool
    ) -> bool:

        query = """
            UPDATE product_variants
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (int(is_active), variant_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists_by_sku(self, sku: str) -> bool:

        query = """
            SELECT 1
            FROM product_variants
            WHERE sku = ?
            LIMIT 1
        """

        with self.connection() as connection:

            return connection.execute(
                query, (sku.strip(),)
            ).fetchone() is not None

    def exists_combination(
        self,
        product_id: int,
        color_id: Optional[int],
        size_id: Optional[int]
    ) -> bool:

        query = """
            SELECT 1
            FROM product_variants
            WHERE product_id = ?
              AND color_id IS ?
              AND size_id IS ?
            LIMIT 1
        """

        with self.connection() as connection:

            return connection.execute(
                query,
                (product_id, color_id, size_id)
            ).fetchone() is not None
