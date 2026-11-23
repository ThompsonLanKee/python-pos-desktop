
import sqlite3
from typing import Optional

from src.models import SalesReturn
from src.repositories.base_repository import BaseRepository


class SalesReturnRepository(BaseRepository):
    """Handles sales return header database operations."""

    def create(
        self,
        sales_return: SalesReturn,
        connection: Optional[sqlite3.Connection] = None,
    ) -> int:

        query = """
            INSERT INTO sales_returns (
                return_number,
                sale_id,
                processed_by,
                return_status,
                total_refund_amount,
                reason,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:
            cursor = db_connection.execute(
                query,
                (
                    sales_return.return_number,
                    sales_return.sale_id,
                    sales_return.processed_by,
                    sales_return.return_status,
                    sales_return.total_refund_amount,
                    sales_return.reason,
                    sales_return.notes,
                ),
            )
            return cursor.lastrowid

    def get_by_id(self, return_id: int) -> Optional[SalesReturn]:

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sales_returns
                WHERE return_id = ?
                """,
                (return_id,),
            ).fetchone()

            return SalesReturn(**dict(row)) if row else None

    def get_by_return_number(
        self,
        return_number: str,
    ) -> Optional[SalesReturn]:

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sales_returns
                WHERE return_number = ?
                """,
                (return_number.strip(),),
            ).fetchone()

            return SalesReturn(**dict(row)) if row else None

    def get_by_sale(self, sale_id: int) -> list[SalesReturn]:

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sales_returns
                WHERE sale_id = ?
                ORDER BY return_id DESC
                """,
                (sale_id,),
            ).fetchall()

            return [
                SalesReturn(**dict(row))
                for row in rows
            ]

    def get_all(self) -> list[dict]:

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    sr.*,
                    s.sale_number
                FROM sales_returns sr
                INNER JOIN sales s
                    ON sr.sale_id = s.sale_id
                ORDER BY sr.return_id DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def update_status(
        self,
        return_id: int,
        return_status: str,
        connection: Optional[sqlite3.Connection] = None,
    ) -> bool:

        return_status = return_status.strip().upper()

        if return_status not in SalesReturn.VALID_STATUSES:
            raise ValueError("Invalid return status.")

        with self.connection_scope(connection) as db_connection:
            cursor = db_connection.execute(
                """
                UPDATE sales_returns
                SET return_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE return_id = ?
                """,
                (return_status, return_id),
            )

            return cursor.rowcount > 0

    def exists(self, return_id: int) -> bool:

        with self.connection() as connection:
            return connection.execute(
                """
                SELECT 1
                FROM sales_returns
                WHERE return_id = ?
                LIMIT 1
                """,
                (return_id,),
            ).fetchone() is not None

    def exists_by_return_number(self, return_number: str) -> bool:

        with self.connection() as connection:
            return connection.execute(
                """
                SELECT 1
                FROM sales_returns
                WHERE return_number = ?
                LIMIT 1
                """,
                (return_number.strip(),),
            ).fetchone() is not None
