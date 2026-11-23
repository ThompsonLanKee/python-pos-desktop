
import sqlite3
from typing import Optional

from src.models import SalesReturnItem
from src.repositories.base_repository import BaseRepository


class SalesReturnItemRepository(BaseRepository):
    """Handles returned product item database operations."""

    def create(
        self,
        item: SalesReturnItem,
        connection: Optional[sqlite3.Connection] = None,
    ) -> int:

        query = """
            INSERT INTO sales_return_items (
                return_id,
                sale_item_id,
                variant_id,
                quantity,
                unit_refund_amount,
                line_refund_amount,
                restock,
                condition,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:
            cursor = db_connection.execute(
                query,
                (
                    item.return_id,
                    item.sale_item_id,
                    item.variant_id,
                    item.quantity,
                    item.unit_refund_amount,
                    item.line_refund_amount,
                    item.restock,
                    item.condition,
                    item.notes,
                ),
            )

            return cursor.lastrowid

    def get_by_id(
        self,
        return_item_id: int,
    ) -> Optional[SalesReturnItem]:

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sales_return_items
                WHERE return_item_id = ?
                """,
                (return_item_id,),
            ).fetchone()

            return SalesReturnItem(**dict(row)) if row else None

    def get_by_return(
        self,
        return_id: int,
    ) -> list[SalesReturnItem]:

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sales_return_items
                WHERE return_id = ?
                ORDER BY return_item_id
                """,
                (return_id,),
            ).fetchall()

            return [
                SalesReturnItem(**dict(row))
                for row in rows
            ]

    def get_by_sale_item(
        self,
        sale_item_id: int,
    ) -> list[dict]:

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    sri.*,
                    sr.return_number,
                    sr.return_status
                FROM sales_return_items sri
                INNER JOIN sales_returns sr
                    ON sri.return_id = sr.return_id
                WHERE sri.sale_item_id = ?
                ORDER BY sri.return_item_id DESC
                """,
                (sale_item_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_returned_quantity(
        self,
        sale_item_id: int,
        connection: Optional[sqlite3.Connection] = None,
    ) -> int:
        """
        Count quantities from completed returns only.
        Voided returns do not consume the returnable quantity.
        """

        with self.connection_scope(connection) as db_connection:
            row = db_connection.execute(
                """
                SELECT COALESCE(SUM(sri.quantity), 0) AS returned_quantity
                FROM sales_return_items sri
                INNER JOIN sales_returns sr
                    ON sri.return_id = sr.return_id
                WHERE sri.sale_item_id = ?
                  AND sr.return_status = 'COMPLETED'
                """,
                (sale_item_id,),
            ).fetchone()

            return int(row["returned_quantity"])

    def get_all(self) -> list[dict]:

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    sri.*,
                    sr.return_number,
                    si.sale_id,
                    si.sku,
                    si.product_name
                FROM sales_return_items sri
                INNER JOIN sales_returns sr
                    ON sri.return_id = sr.return_id
                INNER JOIN sale_items si
                    ON sri.sale_item_id = si.sale_item_id
                ORDER BY sri.return_item_id DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def count_by_return(self, return_id: int) -> int:

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS item_count
                FROM sales_return_items
                WHERE return_id = ?
                """,
                (return_id,),
            ).fetchone()

            return int(row["item_count"])
