
import sqlite3
from typing import Optional

from src.models import Sale
from src.repositories.base_repository import BaseRepository


class SaleRepository(BaseRepository):
    """Handles POS sale header database operations."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        sale: Sale,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a sale header."""

        query = """
            INSERT INTO sales (
                sale_number,
                customer_id,
                cashier_user_id,
                subtotal,
                discount_amount,
                tax_amount,
                total_amount,
                sale_status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    sale.sale_number,
                    sale.customer_id,
                    sale.cashier_user_id,
                    sale.subtotal,
                    sale.discount_amount,
                    sale.tax_amount,
                    sale.total_amount,
                    sale.sale_status,
                    sale.notes
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        sale_id: int
    ) -> Optional[Sale]:
        """Retrieve a sale by its ID."""

        query = """
            SELECT *
            FROM sales
            WHERE sale_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_id,)
            ).fetchone()

            return Sale(**dict(row)) if row else None

    # ==========================================
    # RETRIEVE BY SALE NUMBER
    # ==========================================

    def get_by_sale_number(
        self,
        sale_number: str
    ) -> Optional[Sale]:
        """Retrieve a sale by receipt number."""

        query = """
            SELECT *
            FROM sales
            WHERE sale_number = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_number.strip(),)
            ).fetchone()

            return Sale(**dict(row)) if row else None

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[Sale]:
        """Retrieve all sales."""

        query = """
            SELECT *
            FROM sales
            ORDER BY sale_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Sale(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY CUSTOMER
    # ==========================================

    def get_by_customer(
        self,
        customer_id: int
    ) -> list[Sale]:
        """Retrieve sales belonging to a customer."""

        query = """
            SELECT *
            FROM sales
            WHERE customer_id = ?
            ORDER BY sale_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (customer_id,)
            ).fetchall()

            return [
                Sale(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY CASHIER
    # ==========================================

    def get_by_cashier(
        self,
        cashier_user_id: int
    ) -> list[Sale]:
        """Retrieve sales processed by a cashier."""

        query = """
            SELECT *
            FROM sales
            WHERE cashier_user_id = ?
            ORDER BY sale_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (cashier_user_id,)
            ).fetchall()

            return [
                Sale(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY DATE
    # ==========================================

    def get_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> list[Sale]:
        """
        Retrieve sales within a date range.

        Dates should use YYYY-MM-DD format.
        """

        query = """
            SELECT *
            FROM sales
            WHERE date(created_at) BETWEEN date(?) AND date(?)
            ORDER BY created_at DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (start_date, end_date)
            ).fetchall()

            return [
                Sale(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FILTER BY STATUS
    # ==========================================

    def get_by_status(
        self,
        sale_status: str
    ) -> list[Sale]:

        sale_status = sale_status.strip().upper()

        if sale_status not in Sale.VALID_STATUSES:
            raise ValueError("Invalid sale status.")

        query = """
            SELECT *
            FROM sales
            WHERE sale_status = ?
            ORDER BY sale_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (sale_status,)
            ).fetchall()

            return [
                Sale(**dict(row))
                for row in rows
            ]

    # ==========================================
    # UPDATE STATUS
    # ==========================================

    def update_status(
        self,
        sale_id: int,
        sale_status: str,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update a sale's status."""

        sale_status = sale_status.strip().upper()

        if sale_status not in Sale.VALID_STATUSES:
            raise ValueError("Invalid sale status.")

        query = """
            UPDATE sales
            SET sale_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE sale_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (sale_status, sale_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists(self, sale_id: int) -> bool:
        """Check whether a sale exists."""

        query = """
            SELECT 1
            FROM sales
            WHERE sale_id = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_id,)
            ).fetchone()

            return row is not None

    def exists_by_sale_number(
        self,
        sale_number: str
    ) -> bool:
        """Check whether a receipt number already exists."""

        query = """
            SELECT 1
            FROM sales
            WHERE sale_number = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (sale_number.strip(),)
            ).fetchone()

            return row is not None
