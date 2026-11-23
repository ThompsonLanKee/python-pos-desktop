
import sqlite3
from typing import Optional

from src.models import Refund
from src.repositories.base_repository import BaseRepository


class RefundRepository(BaseRepository):
    """Handles refund database operations."""

    def create(
        self,
        refund: Refund,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:

        query = """
            INSERT INTO refunds (
                payment_id,
                sale_id,
                return_id,
                amount,
                reference_number,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:
            cursor = db_connection.execute(
                query,
                (
                    refund.payment_id,
                    refund.sale_id,
                    refund.return_id,
                    refund.amount,
                    refund.reference_number,
                    refund.notes,
                )
            )

            return cursor.lastrowid

    def get_by_id(self, refund_id: int) -> Optional[Refund]:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM refunds
                WHERE refund_id = ?
                """,
                (refund_id,)
            ).fetchone()

            return Refund(**dict(row)) if row else None

    def get_by_payment(self, payment_id: int) -> list[Refund]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM refunds
                WHERE payment_id = ?
                ORDER BY refund_id DESC
                """,
                (payment_id,)
            ).fetchall()

            return [Refund(**dict(row)) for row in rows]

    def get_by_sale(self, sale_id: int) -> list[Refund]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM refunds
                WHERE sale_id = ?
                ORDER BY refund_id DESC
                """,
                (sale_id,)
            ).fetchall()

            return [Refund(**dict(row)) for row in rows]

    def get_by_return(self, return_id: int) -> list[Refund]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM refunds
                WHERE return_id = ?
                ORDER BY refund_id DESC
                """,
                (return_id,)
            ).fetchall()

            return [Refund(**dict(row)) for row in rows]

    def get_all(self) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    r.*,
                    p.payment_method,
                    p.amount AS original_payment_amount,
                    s.sale_number,
                    sr.return_number
                FROM refunds r
                INNER JOIN payments p
                    ON r.payment_id = p.payment_id
                INNER JOIN sales s
                    ON r.sale_id = s.sale_id
                LEFT JOIN sales_returns sr
                    ON r.return_id = sr.return_id
                ORDER BY r.refund_id DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def get_total_by_payment(
        self,
        payment_id: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        with self.connection_scope(connection) as db_connection:
            row = db_connection.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS refunded_amount
                FROM refunds
                WHERE payment_id = ?
                """,
                (payment_id,)
            ).fetchone()

            return int(row["refunded_amount"])

    def get_total_by_return(
        self,
        return_id: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        with self.connection_scope(connection) as db_connection:
            row = db_connection.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS refunded_amount
                FROM refunds
                WHERE return_id = ?
                """,
                (return_id,)
            ).fetchone()

            return int(row["refunded_amount"])
