
import sqlite3
from typing import Optional

from src.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository):
    """
    Handles inventory balance operations.

    Each product variant has one inventory record.
    """

    # ==========================================
    # INITIALIZE INVENTORY
    # ==========================================

    def create(
        self,
        variant_id: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create an inventory record for a variant."""

        query = """
            INSERT INTO inventory (
                variant_id,
                quantity_on_hand,
                reorder_level
            )
            VALUES (?, 0, 0)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (variant_id,)
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_by_variant(
        self,
        variant_id: int
    ) -> Optional[dict]:
        """Retrieve inventory by variant ID."""

        query = """
            SELECT *
            FROM inventory
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (variant_id,)
            ).fetchone()

            return dict(row) if row else None

    def get_all(self) -> list[dict]:
        """Retrieve all inventory records with variant details."""

        query = """
            SELECT
            i.*,
            pv.sku,
            pv.barcode,
            pv.is_active,
            pv.cost_price,
            pv.selling_price,
            p.product_name,
            cat.category_name,
            col.color_name,
            col.hex_code,
            sz.size_name

            FROM inventory i

            INNER JOIN product_variants pv
                ON i.variant_id = pv.variant_id

            INNER JOIN products p
                ON pv.product_id = p.product_id

            LEFT JOIN categories cat
                ON p.category_id = cat.category_id

            LEFT JOIN colors col
                ON pv.color_id = col.color_id

            LEFT JOIN sizes sz
                ON pv.size_id = sz.size_id

            ORDER BY p.product_name, pv.sku
            """

        with self.connection() as connection:
            rows = connection.execute(query).fetchall()

            return [dict(row) for row in rows]

    def get_low_stock(self) -> list[dict]:
        """Retrieve inventory at or below reorder level."""

        query = """
            SELECT
                i.*,
                pv.sku,
                pv.barcode,
                pv.cost_price,
                pv.selling_price,
                p.product_name,
                col.color_name,
                col.hex_code,
                sz.size_name

            FROM inventory i

            INNER JOIN product_variants pv
                ON i.variant_id = pv.variant_id

            INNER JOIN products p
                ON pv.product_id = p.product_id

            LEFT JOIN colors col
                ON pv.color_id = col.color_id

            LEFT JOIN sizes sz
                ON pv.size_id = sz.size_id

            WHERE i.quantity_on_hand <= i.reorder_level

            ORDER BY i.quantity_on_hand, p.product_name
        """

        with self.connection() as connection:
            rows = connection.execute(query).fetchall()

            return [dict(row) for row in rows]

    # ==========================================
    # UPDATE
    # ==========================================

    def update_quantity(
        self,
        variant_id: int,
        quantity: int
    ) -> bool:
        """Set the current stock quantity."""

        if quantity < 0:
            raise ValueError(
                "Stock quantity cannot be negative."
            )

        query = """
            UPDATE inventory
            SET quantity_on_hand = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (quantity, variant_id)
            )

            return cursor.rowcount > 0

    def adjust_quantity(
        self,
        variant_id: int,
        quantity_change: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """
        Adjust stock atomically.

        Uses an existing transaction when a connection is supplied.
        Prevents the balance from becoming negative.
        """

        if (
            not isinstance(quantity_change, int)
            or isinstance(quantity_change, bool)
        ):
            raise TypeError("Stock adjustment must be an integer.")

        if quantity_change == 0:
            raise ValueError("Stock adjustment cannot be zero.")

        query = """
            UPDATE inventory
            SET quantity_on_hand = quantity_on_hand + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
              AND quantity_on_hand + ? >= 0
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    quantity_change,
                    variant_id,
                    quantity_change
                )
            )

            return cursor.rowcount > 0

    def update_reorder_level(
        self,
        variant_id: int,
        reorder_level: int
    ) -> bool:
        """Update the minimum stock alert level."""

        if reorder_level < 0:
            raise ValueError(
                "Reorder level cannot be negative."
            )

        query = """
            UPDATE inventory
            SET reorder_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (reorder_level, variant_id)
            )

            return cursor.rowcount > 0
