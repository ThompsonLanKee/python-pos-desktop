
import sqlite3
from typing import Optional

from src.models import SaleItem
from src.repositories.base_repository import BaseRepository


class SaleItemRepository(BaseRepository):
    """Handles sale item database operations."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        item: SaleItem,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a sale item."""

        query = """
            INSERT INTO sale_items (
                sale_id,
                variant_id,
                product_name,
                sku,
                quantity,
                unit_cost,
                unit_price,
                discount_amount,
                line_total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    item.sale_id,
                    item.variant_id,
                    item.product_name,
                    item.sku,
                    item.quantity,
                    item.unit_cost,
                    item.unit_price,
                    item.discount_amount,
                    item.line_total
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        sale_item_id: int
    ) -> Optional[SaleItem]:

        query = """
            SELECT *
            FROM sale_items
            WHERE sale_item_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_item_id,)
            ).fetchone()

            return SaleItem(**dict(row)) if row else None

    # ==========================================
    # RETRIEVE BY SALE
    # ==========================================

    def get_by_sale(
        self,
        sale_id: int
    ) -> list[SaleItem]:

        query = """
            SELECT *
            FROM sale_items
            WHERE sale_id = ?
            ORDER BY sale_item_id
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (sale_id,)
            ).fetchall()

            return [
                SaleItem(**dict(row))
                for row in rows
            ]

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[dict]:

        query = """
            SELECT
                si.*,
                s.sale_number

            FROM sale_items si

            INNER JOIN sales s
                ON si.sale_id = s.sale_id

            ORDER BY si.sale_item_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # ==========================================
    # DELETE BY SALE
    # ==========================================

    def delete_by_sale(
        self,
        sale_id: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """
        Delete sale items belonging to a sale.

        Intended for use inside a transaction when
        removing an uncommitted draft sale.
        """

        query = """
            DELETE FROM sale_items
            WHERE sale_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (sale_id,)
            )

            return cursor.rowcount

    # ==========================================
    # VALIDATION
    # ==========================================

    def exists(self, sale_item_id: int) -> bool:

        query = """
            SELECT 1
            FROM sale_items
            WHERE sale_item_id = ?
            LIMIT 1
        """

        with self.connection() as connection:

            return connection.execute(
                query,
                (sale_item_id,)
            ).fetchone() is not None

    def count_by_sale(self, sale_id: int) -> int:

        query = """
            SELECT COUNT(*) AS item_count
            FROM sale_items
            WHERE sale_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_id,)
            ).fetchone()

            return row["item_count"]
