
import sqlite3
from typing import Optional

from src.models import Customer
from src.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    """Handles customer database operations."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        customer: Customer,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Create a new customer."""

        query = """
            INSERT INTO customers (
                customer_name,
                phone,
                email,
                address,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    customer.customer_name,
                    customer.phone,
                    customer.email,
                    customer.address,
                    customer.is_active
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        customer_id: int
    ) -> Optional[Customer]:
        """Retrieve a customer by ID."""

        query = """
            SELECT *
            FROM customers
            WHERE customer_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (customer_id,)
            ).fetchone()

            return Customer(**dict(row)) if row else None

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[Customer]:
        """Retrieve all customers."""

        query = """
            SELECT *
            FROM customers
            ORDER BY customer_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Customer(**dict(row))
                for row in rows
            ]

    # ==========================================
    # RETRIEVE ACTIVE CUSTOMERS
    # ==========================================

    def get_active(self) -> list[Customer]:
        """Retrieve active customers."""

        query = """
            SELECT *
            FROM customers
            WHERE is_active = 1
            ORDER BY customer_name
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Customer(**dict(row))
                for row in rows
            ]

    # ==========================================
    # SEARCH
    # ==========================================

    def search(self, keyword: str) -> list[Customer]:
        """Search customers by name, phone, or email."""

        keyword = keyword.strip()

        if not keyword:
            return []

        search_term = f"%{keyword}%"

        query = """
            SELECT *
            FROM customers
            WHERE customer_name LIKE ?
               OR phone LIKE ?
               OR email LIKE ?
            ORDER BY customer_name
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (
                    search_term,
                    search_term,
                    search_term
                )
            ).fetchall()

            return [
                Customer(**dict(row))
                for row in rows
            ]

    # ==========================================
    # FIND BY PHONE
    # ==========================================

    def get_by_phone(
        self,
        phone: str
    ) -> Optional[Customer]:
        """Retrieve a customer by phone number."""

        query = """
            SELECT *
            FROM customers
            WHERE phone = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (phone.strip(),)
            ).fetchone()

            return Customer(**dict(row)) if row else None

    # ==========================================
    # UPDATE
    # ==========================================

    def update(
        self,
        customer: Customer,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update customer information."""

        if customer.customer_id is None:
            raise ValueError("Customer ID is required.")

        query = """
            UPDATE customers
            SET customer_name = ?,
                phone = ?,
                email = ?,
                address = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    customer.customer_name,
                    customer.phone,
                    customer.email,
                    customer.address,
                    customer.customer_id
                )
            )

            return cursor.rowcount > 0

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    def set_active(
        self,
        customer_id: int,
        is_active: bool,
        connection: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Activate or deactivate a customer."""

        query = """
            UPDATE customers
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = ?
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (int(is_active), customer_id)
            )

            return cursor.rowcount > 0

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def exists(self, customer_id: int) -> bool:
        """Check whether a customer exists."""

        query = """
            SELECT 1
            FROM customers
            WHERE customer_id = ?
            LIMIT 1
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (customer_id,)
            ).fetchone()

            return row is not None

    def exists_by_phone(
        self,
        phone: str,
        exclude_customer_id: Optional[int] = None
    ) -> bool:
        """Check whether a phone number is already registered."""

        if exclude_customer_id is None:
            query = """
                SELECT 1
                FROM customers
                WHERE phone = ?
                LIMIT 1
            """
            parameters = (phone.strip(),)

        else:
            query = """
                SELECT 1
                FROM customers
                WHERE phone = ?
                  AND customer_id != ?
                LIMIT 1
            """
            parameters = (
                phone.strip(),
                exclude_customer_id
            )

        with self.connection() as connection:

            row = connection.execute(
                query,
                parameters
            ).fetchone()

            return row is not None
