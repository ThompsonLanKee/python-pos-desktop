
import sqlite3
from typing import Optional

from src.models import ProductVariant
from src.repositories.base_repository import BaseRepository


class ProductVariantRepository(BaseRepository):
    """
    Handles product variant database operations.

    Each variant belongs to one product and has:
    - Unique SKU
    - Optional barcode
    - Optional color and size
    - Cost and selling prices
    - Active/inactive status

    Supports shared database transactions.
    """

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        variant: ProductVariant,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a new product variant."""

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

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
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
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        variant_id: int
    ) -> Optional[ProductVariant]:
        """Retrieve a variant by its ID."""

        query = """
            SELECT *
            FROM product_variants
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (variant_id,)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    # ==========================================
    # RETRIEVE BY SKU
    # ==========================================

    def get_by_sku(
        self,
        sku: str
    ) -> Optional[ProductVariant]:
        """Retrieve a variant by SKU (case-insensitive)."""

        query = """
            SELECT *
            FROM product_variants
            WHERE sku = ? COLLATE NOCASE
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sku.strip(),)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    # ==========================================
    # RETRIEVE BY BARCODE
    # ==========================================

    def get_by_barcode(
        self,
        barcode: str
    ) -> Optional[ProductVariant]:
        """Retrieve a variant by barcode."""

        query = """
            SELECT *
            FROM product_variants
            WHERE barcode = ? COLLATE NOCASE
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (barcode.strip(),)
            ).fetchone()

            return (
                ProductVariant(**dict(row))
                if row else None
            )

    # ==========================================
    # RETRIEVE BY PRODUCT
    # ==========================================

    def get_by_product(
        self,
        product_id: int
    ) -> list[ProductVariant]:
        """Retrieve all variants belonging to a product."""

        query = """
            SELECT *
            FROM product_variants
            WHERE product_id = ?
            ORDER BY variant_id
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (product_id,)
            ).fetchall()

            return [
                ProductVariant(**dict(row))
                for row in rows
            ]

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[ProductVariant]:
        """Retrieve all product variants."""

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
    # RETRIEVE ACTIVE VARIANTS
    # ==========================================

    def get_active(self) -> list[ProductVariant]:
        """Retrieve active variants only."""

        query = """
            SELECT *
            FROM product_variants
            WHERE is_active = 1
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

    def update(
        self,
        variant: ProductVariant,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update variant information."""

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

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
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
        is_active: bool,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Activate or deactivate a product variant."""

        query = """
            UPDATE product_variants
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (int(is_active), variant_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # VALIDATION: SKU
    # ==========================================

    def exists_by_sku(
        self,
        sku: str,
        exclude_variant_id: Optional[int] = None,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Check whether an SKU already exists."""

        query = """
            SELECT 1
            FROM product_variants
            WHERE sku = ? COLLATE NOCASE
        """

        parameters = [sku.strip()]

        if exclude_variant_id is not None:
            query += " AND variant_id != ?"
            parameters.append(exclude_variant_id)

        query += " LIMIT 1"

        with self.connection_scope(connection) as db_connection:

            return db_connection.execute(
                query,
                parameters
            ).fetchone() is not None

    # ==========================================
    # VALIDATION: BARCODE
    # ==========================================

    def exists_by_barcode(
        self,
        barcode: str,
        exclude_variant_id: Optional[int] = None,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Check whether a barcode already exists."""

        query = """
            SELECT 1
            FROM product_variants
            WHERE barcode = ? COLLATE NOCASE
        """

        parameters = [barcode.strip()]

        if exclude_variant_id is not None:
            query += " AND variant_id != ?"
            parameters.append(exclude_variant_id)

        query += " LIMIT 1"

        with self.connection_scope(connection) as db_connection:

            return db_connection.execute(
                query,
                parameters
            ).fetchone() is not None

    # ==========================================
    # VALIDATION: VARIANT COMBINATION
    # ==========================================

    def exists_combination(
        self,
        product_id: int,
        color_id: Optional[int],
        size_id: Optional[int],
        exclude_variant_id: Optional[int] = None,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """
        Check whether a product already has
        the specified color and size combination.

        Can exclude an existing variant during updates.
        """

        query = """
            SELECT 1
            FROM product_variants
            WHERE product_id = ?
              AND color_id IS ?
              AND size_id IS ?
        """

        parameters = [
            product_id,
            color_id,
            size_id
        ]

        if exclude_variant_id is not None:
            query += " AND variant_id != ?"
            parameters.append(exclude_variant_id)

        query += " LIMIT 1"

        with self.connection_scope(connection) as db_connection:

            return db_connection.execute(
                query,
                parameters
            ).fetchone() is not None
