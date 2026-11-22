
import sqlite3
from typing import Optional

from src.models import InventoryTransaction
from src.repositories.base_repository import BaseRepository


class InventoryTransactionRepository(BaseRepository):
    """Handles inventory transaction history."""

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        transaction: InventoryTransaction,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Record an inventory movement."""

        query = """
            INSERT INTO inventory_transactions (
                variant_id,
                transaction_type,
                quantity_change,
                quantity_after,
                reference_type,
                reference_id,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection_scope(connection) as db_connection:

            cursor = db_connection.execute(
                query,
                (
                    transaction.variant_id,
                    transaction.transaction_type,
                    transaction.quantity_change,
                    transaction.quantity_after,
                    transaction.reference_type,
                    transaction.reference_id,
                    transaction.notes
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    def get_by_id(
        self,
        transaction_id: int
    ) -> Optional[InventoryTransaction]:

        query = """
            SELECT *
            FROM inventory_transactions
            WHERE transaction_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (transaction_id,)
            ).fetchone()

            return (
                InventoryTransaction(**dict(row))
                if row else None
            )

    # ==========================================
    # RETRIEVE BY VARIANT
    # ==========================================

    def get_by_variant(
        self,
        variant_id: int
    ) -> list[InventoryTransaction]:

        query = """
            SELECT *
            FROM inventory_transactions
            WHERE variant_id = ?
            ORDER BY transaction_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (variant_id,)
            ).fetchall()

            return [
                InventoryTransaction(**dict(row))
                for row in rows
            ]

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    def get_all(self) -> list[dict]:

        query = """
            SELECT
                t.*,
                pv.sku,
                p.product_name

            FROM inventory_transactions t

            INNER JOIN product_variants pv
                ON t.variant_id = pv.variant_id

            INNER JOIN products p
                ON pv.product_id = p.product_id

            ORDER BY t.transaction_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # ==========================================
    # FILTER BY TYPE
    # ==========================================

    def get_by_type(
        self,
        transaction_type: str
    ) -> list[InventoryTransaction]:

        transaction_type = transaction_type.strip().upper()

        query = """
            SELECT *
            FROM inventory_transactions
            WHERE transaction_type = ?
            ORDER BY transaction_id DESC
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (transaction_type,)
            ).fetchall()

            return [
                InventoryTransaction(**dict(row))
                for row in rows
            ]
