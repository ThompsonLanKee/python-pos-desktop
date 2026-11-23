
from src.core.database import Database
from src.models import SalesReturn, SalesReturnItem
from src.repositories import (
    SalesReturnRepository,
    SalesReturnItemRepository,
)


class SalesReturnService:
    """Handles physical product returns and eligible stock restoration."""

    def __init__(self, database: Database):
        self.database = database
        self.return_repository = SalesReturnRepository(database)
        self.item_repository = SalesReturnItemRepository(database)

    @staticmethod
    def _validate_positive_id(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(f"{field_name} must be a positive integer.")

    @staticmethod
    def _validate_quantity(value):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError("Return quantity must be a positive integer.")

    @staticmethod
    def _allocate_refund(
        line_total: int,
        original_quantity: int,
        previously_returned: int,
        return_quantity: int,
    ) -> int:
        """
        Allocate the original discounted line total proportionally.

        Cumulative rounding ensures that multiple partial returns
        never refund more than the original sale item's line total.
        """

        before = (
            line_total * previously_returned
        ) // original_quantity

        after = (
            line_total * (previously_returned + return_quantity)
        ) // original_quantity

        return after - before

    # ==========================================
    # CREATE RETURN
    # ==========================================

    def create_return(
        self,
        return_number: str,
        sale_id: int,
        items: list[dict],
        processed_by: int | None = None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Create a physical return.

        Each item dictionary requires:
            sale_item_id
            quantity

        Optional:
            restock: bool, defaults to True
            condition: GOOD, DAMAGED, or DEFECTIVE
            notes

        Monetary refunds are not issued here.
        The returned amount is recorded for later refund processing.
        """

        if not isinstance(return_number, str) or not return_number.strip():
            raise ValueError("Return number is required.")

        self._validate_positive_id(sale_id, "Sale ID")

        if processed_by is not None:
            self._validate_positive_id(processed_by, "Processed-by user ID")

        if not isinstance(items, list) or not items:
            raise ValueError("At least one returned item is required.")

        if not all(isinstance(item, dict) for item in items):
            raise TypeError("Each return item must be a dictionary.")

        prepared_items = []
        total_refund_amount = 0

        with self.database.transaction() as connection:

            # 1. Validate the original sale.
            sale = connection.execute(
                """
                SELECT sale_id, sale_status
                FROM sales
                WHERE sale_id = ?
                """,
                (sale_id,),
            ).fetchone()

            if sale is None:
                raise ValueError("Original sale does not exist.")

            if sale["sale_status"] == "VOIDED":
                raise ValueError("Cannot return items from a voided sale.")

            if sale["sale_status"] == "REFUNDED":
                raise ValueError("This sale has already been refunded.")

            # 2. Prevent duplicate sale-item entries in one return.
            sale_item_ids = []

            for item in items:
                sale_item_id = item.get("sale_item_id")
                self._validate_positive_id(
                    sale_item_id,
                    "Sale item ID",
                )

                if sale_item_id in sale_item_ids:
                    raise ValueError(
                        "A sale item cannot appear twice in one return."
                    )

                sale_item_ids.append(sale_item_id)

            # 3. Validate and calculate every return item.
            for item in items:
                sale_item_id = item["sale_item_id"]
                quantity = item.get("quantity")

                self._validate_quantity(quantity)

                restock_value = item.get("restock", True)

                if not isinstance(restock_value, bool):
                    raise ValueError("Restock must be True or False.")

                restock = int(restock_value)
                condition = item.get("condition", "GOOD").strip().upper()

                if condition not in SalesReturnItem.VALID_CONDITIONS:
                    raise ValueError("Invalid returned item condition.")

                if restock and condition != "GOOD":
                    raise ValueError(
                        "Only goods in GOOD condition can be restocked."
                    )

                sale_item = connection.execute(
                    """
                    SELECT
                        sale_item_id,
                        sale_id,
                        variant_id,
                        quantity,
                        unit_price,
                        line_total
                    FROM sale_items
                    WHERE sale_item_id = ?
                      AND sale_id = ?
                    """,
                    (sale_item_id, sale_id),
                ).fetchone()

                if sale_item is None:
                    raise ValueError(
                        f"Sale item {sale_item_id} does not belong "
                        "to this sale."
                    )

                original_quantity = int(sale_item["quantity"])

                returned_row = connection.execute(
                    """
                    SELECT COALESCE(SUM(sri.quantity), 0)
                        AS returned_quantity
                    FROM sales_return_items sri
                    INNER JOIN sales_returns sr
                        ON sri.return_id = sr.return_id
                    WHERE sri.sale_item_id = ?
                      AND sr.return_status = 'COMPLETED'
                    """,
                    (sale_item_id,),
                ).fetchone()

                previously_returned = int(
                    returned_row["returned_quantity"]
                )

                remaining_quantity = (
                    original_quantity - previously_returned
                )

                if quantity > remaining_quantity:
                    raise ValueError(
                        f"Cannot return {quantity} units of sale item "
                        f"{sale_item_id}. Only {remaining_quantity} "
                        "unit(s) remain returnable."
                    )

                line_refund_amount = self._allocate_refund(
                    line_total=int(sale_item["line_total"]),
                    original_quantity=original_quantity,
                    previously_returned=previously_returned,
                    return_quantity=quantity,
                )

                prepared_items.append({
                    "sale_item_id": sale_item_id,
                    "variant_id": int(sale_item["variant_id"]),
                    "quantity": quantity,
                    "unit_refund_amount": int(sale_item["unit_price"]),
                    "line_refund_amount": line_refund_amount,
                    "restock": restock,
                    "condition": condition,
                    "notes": item.get("notes"),
                })

                total_refund_amount += line_refund_amount

            # 4. Create the return header.
            sales_return = SalesReturn(
                return_number=return_number,
                sale_id=sale_id,
                processed_by=processed_by,
                total_refund_amount=total_refund_amount,
                reason=reason,
                notes=notes,
            )

            return_id = self.return_repository.create(
                sales_return,
                connection=connection,
            )

            # 5. Create return items and restore eligible stock.
            for item in prepared_items:

                return_item = SalesReturnItem(
                    return_id=return_id,
                    sale_item_id=item["sale_item_id"],
                    variant_id=item["variant_id"],
                    quantity=item["quantity"],
                    unit_refund_amount=item["unit_refund_amount"],
                    line_refund_amount=item["line_refund_amount"],
                    restock=item["restock"],
                    condition=item["condition"],
                    notes=item["notes"],
                )

                self.item_repository.create(
                    return_item,
                    connection=connection,
                )

                if item["restock"] == 1:

                    inventory_cursor = connection.execute(
                        """
                        UPDATE inventory
                        SET quantity_on_hand = quantity_on_hand + ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE variant_id = ?
                        """,
                        (
                            item["quantity"],
                            item["variant_id"],
                        ),
                    )

                    if inventory_cursor.rowcount != 1:
                        raise ValueError(
                            "Inventory record does not exist for "
                            f"variant {item['variant_id']}."
                        )

                    quantity_row = connection.execute(
                        """
                        SELECT quantity_on_hand
                        FROM inventory
                        WHERE variant_id = ?
                        """,
                        (item["variant_id"],),
                    ).fetchone()

                    quantity_after = int(
                        quantity_row["quantity_on_hand"]
                    )

                    # Record the inventory movement in the same transaction.
                    connection.execute(
                        """
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
                        """,
                        (
                            item["variant_id"],
                            "SALE_RETURN",
                            item["quantity"],
                            quantity_after,
                            "SALES_RETURN",
                            return_id,
                            f"Restocked from return {return_number}",
                        ),
                    )

            return {
                "return_id": return_id,
                "return_number": return_number,
                "sale_id": sale_id,
                "total_refund_amount": total_refund_amount,
                "item_count": len(prepared_items),
                "message": "Sales return created successfully.",
            }

    # ==========================================
    # GET RETURNABLE QUANTITY
    # ==========================================

    def get_returnable_quantity(self, sale_item_id: int) -> int:

        self._validate_positive_id(sale_item_id, "Sale item ID")

        with self.database.connect() as connection:

            sale_item = connection.execute(
                """
                SELECT quantity
                FROM sale_items
                WHERE sale_item_id = ?
                """,
                (sale_item_id,),
            ).fetchone()

            if sale_item is None:
                raise ValueError("Sale item does not exist.")

            returned = connection.execute(
                """
                SELECT COALESCE(SUM(sri.quantity), 0)
                    AS returned_quantity
                FROM sales_return_items sri
                INNER JOIN sales_returns sr
                    ON sri.return_id = sr.return_id
                WHERE sri.sale_item_id = ?
                  AND sr.return_status = 'COMPLETED'
                """,
                (sale_item_id,),
            ).fetchone()

            return max(
                0,
                int(sale_item["quantity"])
                - int(returned["returned_quantity"]),
            )

    # ==========================================
    # GET RETURN DETAILS
    # ==========================================

    def get_return_details(self, return_id: int) -> dict:

        self._validate_positive_id(return_id, "Return ID")

        with self.database.connect() as connection:

            header = connection.execute(
                """
                SELECT
                    sr.*,
                    s.sale_number
                FROM sales_returns sr
                INNER JOIN sales s
                    ON sr.sale_id = s.sale_id
                WHERE sr.return_id = ?
                """,
                (return_id,),
            ).fetchone()

            if header is None:
                raise ValueError("Sales return does not exist.")

            rows = connection.execute(
                """
                SELECT
                    sri.*,
                    si.product_name,
                    si.sku
                FROM sales_return_items sri
                INNER JOIN sale_items si
                    ON sri.sale_item_id = si.sale_item_id
                WHERE sri.return_id = ?
                ORDER BY sri.return_item_id
                """,
                (return_id,),
            ).fetchall()

            return {
                "return": dict(header),
                "items": [dict(row) for row in rows],
            }

    # ==========================================
    # GET RETURNS BY SALE
    # ==========================================

    def get_returns_by_sale(self, sale_id: int) -> list[dict]:

        self._validate_positive_id(sale_id, "Sale ID")

        with self.database.connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM sales_returns
                WHERE sale_id = ?
                ORDER BY return_id DESC
                """,
                (sale_id,),
            ).fetchall()

            return [dict(row) for row in rows]
