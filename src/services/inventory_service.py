
import sqlite3

from src.core.database import Database
from src.models import InventoryTransaction
from src.repositories import (
    InventoryRepository,
    ProductVariantRepository,
    InventoryTransactionRepository,
)


class InventoryService:
    """
    Handles inventory business logic.

    Each product variant has its own inventory record.

    Supports:
    - Inventory retrieval
    - Stock receiving
    - Stock issuing
    - Manual stock adjustments
    - Reorder level management
    - Low-stock monitoring
    """

    def __init__(self, database: Database):

        self.database = database

        self.inventory_repository = InventoryRepository(database)
        self.variant_repository = ProductVariantRepository(database)
        self.transaction_repository = InventoryTransactionRepository(database)

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        """Validate a positive integer ID."""

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                f"{field_name} must be a positive integer."
            )

    @staticmethod
    def _validate_positive_quantity(quantity: int) -> None:
        """Validate a positive stock quantity."""

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            raise ValueError(
                "Quantity must be a positive integer."
            )

    @staticmethod
    def _validate_non_negative_quantity(quantity: int) -> None:
        """Validate a non-negative stock quantity."""

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 0
        ):
            raise ValueError(
                "Quantity must be a non-negative integer."
            )

    def _require_inventory(self, variant_id: int) -> dict:
        """Retrieve an existing inventory record."""

        inventory = self.inventory_repository.get_by_variant(
            variant_id
        )

        if inventory is None:
            raise ValueError(
                "Inventory record does not exist for this variant."
            )

        return inventory

    # ==========================================
    # RETRIEVE INVENTORY BY VARIANT
    # ==========================================

    def get_inventory(self, variant_id: int) -> dict | None:
        """Retrieve inventory information for a variant."""

        self._validate_positive_id(
            variant_id,
            "Variant ID"
        )

        return self.inventory_repository.get_by_variant(
            variant_id
        )

    # ==========================================
    # RETRIEVE ALL INVENTORY
    # ==========================================

    def get_all_inventory(self) -> list[dict]:
        """Retrieve all inventory records."""

        return self.inventory_repository.get_all()

    # ==========================================
    # RETRIEVE LOW-STOCK ITEMS
    # ==========================================

    def get_low_stock(self) -> list[dict]:
        """
        Retrieve variants whose stock is at or below
        their configured reorder level.
        """

        return self.inventory_repository.get_low_stock()

    # ==========================================
    # RECEIVE STOCK
    # ==========================================

    def receive_stock(
        self,
        variant_id: int,
        quantity: int,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None
    ) -> bool:
        """Receive purchased or additional stock."""

        self._validate_positive_quantity(quantity)

        return self._change_stock(
            variant_id,
            quantity,
            "PURCHASE",
            reference_type,
            reference_id,
            notes
        )

    def issue_stock(
        self,
        variant_id: int,
        quantity: int,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None
    ) -> bool:
        """Issue stock, normally for a sale."""

        self._validate_positive_quantity(quantity)

        return self._change_stock(
            variant_id,
            -quantity,
            "SALE",
            reference_type,
            reference_id,
            notes
        )

    def adjust_stock(
        self,
        variant_id: int,
        quantity_change: int,
        notes: str | None = None
    ) -> bool:
        """Manually increase or decrease stock."""

        if (
            not isinstance(quantity_change, int)
            or isinstance(quantity_change, bool)
        ):
            raise TypeError("Stock adjustment must be an integer.")

        if quantity_change == 0:
            raise ValueError("Stock adjustment cannot be zero.")

        transaction_type = (
            "ADJUSTMENT_IN"
            if quantity_change > 0
            else "ADJUSTMENT_OUT"
        )

        return self._change_stock(
            variant_id,
            quantity_change,
            transaction_type,
            notes=notes
        )

    def record_damage(
        self,
        variant_id: int,
        quantity: int,
        notes: str | None = None
    ) -> bool:
        """Remove damaged stock and record the reason."""

        self._validate_positive_quantity(quantity)

        return self._change_stock(
            variant_id,
            -quantity,
            "DAMAGE",
            notes=notes
        )

    def set_stock_quantity(
        self,
        variant_id: int,
        quantity: int,
        notes: str | None = None
    ) -> bool:
        """Set stock to a counted quantity and record the adjustment."""

        self._validate_non_negative_quantity(quantity)
        self._validate_positive_id(variant_id, "Variant ID")

        try:
            with self.database.transaction() as connection:
                quantity_before = self._get_quantity_for_change(
                    connection,
                    variant_id
                )
                quantity_change = quantity - quantity_before

                if quantity_change == 0:
                    return True

                transaction_type = (
                    "ADJUSTMENT_IN"
                    if quantity_change > 0
                    else "ADJUSTMENT_OUT"
                )

                return self._record_stock_change(
                    connection,
                    variant_id,
                    quantity_before,
                    quantity_change,
                    transaction_type,
                    notes=notes or "Stock count correction"
                )

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to record inventory movement: {error}"
            ) from error

    def get_transaction_history(self, variant_id: int):
        """Retrieve stock movement history for a variant."""

        self._validate_positive_id(variant_id, "Variant ID")

        return self.transaction_repository.get_by_variant(variant_id)

    def get_all_transactions(self) -> list[dict]:
        """Retrieve all inventory movements."""

        return self.transaction_repository.get_all()

    # ==========================================
    # UPDATE REORDER LEVEL
    # ==========================================

    def set_reorder_level(
        self,
        variant_id: int,
        reorder_level: int
    ) -> bool:
        """Update the minimum stock alert level."""

        self._validate_non_negative_quantity(reorder_level)
        self._validate_positive_id(variant_id, "Variant ID")
        self._require_inventory(variant_id)

        return self.inventory_repository.update_reorder_level(
            variant_id,
            reorder_level
        )

    def _change_stock(
        self,
        variant_id: int,
        quantity_change: int,
        transaction_type: str,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None
    ) -> bool:
        """Update stock and record its history atomically."""

        self._validate_positive_id(variant_id, "Variant ID")

        if (
            not isinstance(quantity_change, int)
            or isinstance(quantity_change, bool)
            or quantity_change == 0
        ):
            raise ValueError("Quantity change must be a non-zero integer.")

        transaction_type = transaction_type.strip().upper()

        try:
            with self.database.transaction() as connection:
                quantity_before = self._get_quantity_for_change(
                    connection,
                    variant_id
                )

                return self._record_stock_change(
                    connection,
                    variant_id,
                    quantity_before,
                    quantity_change,
                    transaction_type,
                    reference_type,
                    reference_id,
                    notes
                )

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to record inventory movement: {error}"
            ) from error

    @staticmethod
    def _get_quantity_for_change(
        connection: sqlite3.Connection,
        variant_id: int
    ) -> int:
        variant = connection.execute(
            """
            SELECT variant_id
            FROM product_variants
            WHERE variant_id = ?
              AND is_active = 1
            """,
            (variant_id,)
        ).fetchone()

        if variant is None:
            raise ValueError(
                "Product variant does not exist or is inactive."
            )

        inventory = connection.execute(
            """
            SELECT quantity_on_hand
            FROM inventory
            WHERE variant_id = ?
            """,
            (variant_id,)
        ).fetchone()

        if inventory is None:
            raise ValueError(
                "Inventory record does not exist for this variant."
            )

        return inventory["quantity_on_hand"]

    def _record_stock_change(
        self,
        connection: sqlite3.Connection,
        variant_id: int,
        quantity_before: int,
        quantity_change: int,
        transaction_type: str,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None
    ) -> bool:
        if not self.inventory_repository.adjust_quantity(
            variant_id,
            quantity_change,
            connection=connection
        ):
            return False

        transaction = InventoryTransaction(
            variant_id=variant_id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            quantity_after=quantity_before + quantity_change,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )

        self.transaction_repository.create(
            transaction,
            connection=connection
        )

        return True
