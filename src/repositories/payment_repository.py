
import sqlite3
from typing import Optional

from src.models import Payment
from src.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    """Handles POS payment database operations."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        payment: Payment,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a payment record."""

        query = """
            INSERT INTO payments (
                sale_id,
                payment_method,
                amount,
                payment_status,
                reference_number,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    payment.sale_id,
                    payment.payment_method,
                    payment.amount,
                    payment.payment_status,
                    payment.reference_number,
                    payment.notes
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        payment_id: int
    ) -> Optional[Payment]:
        """Retrieve a payment by its ID."""

        query = """
            SELECT *
            FROM payments
            WHERE payment_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (payment_id,)
            ).fetchone()

            return Payment(**dict(row)) if row else None

    # ==========================================
    # RETRIEVE BY SALE
    # ==========================================

    def get_by_sale(
        self,
        sale_id: int
    ) -> list[Payment]:
        """Retrieve all payments belonging to a sale."""

        query = """
            SELECT *
            FROM payments
            WHERE sale_id = ?
            ORDER BY payment_id
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (sale_id,)
            ).fetchall()

            return [
                Payment(**dict(row))
                for row in rows
            ]

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[Payment]:
        """Retrieve all payment records."""

        query = """
            SELECT *
            FROM payments
            ORDER BY payment_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Payment(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY METHOD
    # ==========================================

    def get_by_method(
        self,
        payment_method: str
    ) -> list[Payment]:
        """Retrieve payments by payment method."""

        payment_method = payment_method.strip().upper()

        if payment_method not in Payment.VALID_METHODS:
            raise ValueError("Invalid payment method.")

        query = """
            SELECT *
            FROM payments
            WHERE payment_method = ?
            ORDER BY payment_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (payment_method,)
            ).fetchall()

            return [
                Payment(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY STATUS
    # ==========================================

    def get_by_status(
        self,
        payment_status: str
    ) -> list[Payment]:
        """Retrieve payments by payment status."""

        payment_status = payment_status.strip().upper()

        if payment_status not in Payment.VALID_STATUSES:
            raise ValueError("Invalid payment status.")

        query = """
            SELECT *
            FROM payments
            WHERE payment_status = ?
            ORDER BY payment_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (payment_status,)
            ).fetchall()

            return [
                Payment(**dict(row))
                for row in rows
            ]

    # ==========================================
    # UPDATE STATUS
    # ==========================================

    def update_status(
        self,
        payment_id: int,
        payment_status: str,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update a payment status."""

        payment_status = payment_status.strip().upper()

        if payment_status not in Payment.VALID_STATUSES:
            raise ValueError("Invalid payment status.")

        query = """
            UPDATE payments
            SET payment_status = ?
            WHERE payment_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (payment_status, payment_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # PAYMENT TOTALS
    # ==========================================

    def get_completed_total_by_sale(
        self,
        sale_id: int,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """
        Calculate the total of completed payments for a sale.

        Useful when validating whether a sale has been fully paid.
        """

        query = """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM payments
            WHERE sale_id = ?
              AND payment_status = 'COMPLETED'
        """

        with self.connection_scope(connection) as db_connection:

            row = db_connection.execute(
                query,
                (sale_id,)
            ).fetchone()

            return int(row["total"])

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists(self, payment_id: int) -> bool:
        """Check whether a payment exists."""

        query = """
            SELECT 1
            FROM payments
            WHERE payment_id = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (payment_id,)
            ).fetchone()

            return row is not None

    def count_by_sale(self, sale_id: int) -> int:
        """Count payment records belonging to a sale."""

        query = """
            SELECT COUNT(*) AS payment_count
            FROM payments
            WHERE sale_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_id,)
            ).fetchone()

            return row["payment_count"]
