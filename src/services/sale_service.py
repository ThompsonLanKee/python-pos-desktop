
import sqlite3
from contextlib import closing
from typing import Optional

from src.core.database import Database
from src.models import Sale, SaleItem, Payment, InventoryTransaction
from src.repositories import (
    SaleRepository,
    SaleItemRepository,
    InventoryRepository,
    InventoryTransactionRepository,
    PaymentRepository,
)


class SaleService:
    """
    Coordinates POS checkout operations.

    A checkout transaction includes:
    - Sale creation
    - Sale item creation
    - Inventory deduction
    - Inventory movement history
    - Optional payment recording

    All operations succeed or roll back together.
    """

    def __init__(self, database: Database):
        self.database = database

        self.sale_repository = SaleRepository(database)
        self.sale_item_repository = SaleItemRepository(database)
        self.inventory_repository = InventoryRepository(database)
        self.transaction_repository = InventoryTransactionRepository(database)
        self.payment_repository = PaymentRepository(database)

    # ==========================================
    # VALIDATION
    # ==========================================

    @staticmethod
    def _validate_positive_integer(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                f"{field_name} must be a positive integer."
            )

    @staticmethod
    def _validate_non_negative_integer(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(
                f"{field_name} must be a non-negative integer."
            )

    # ==========================================
    # CREATE SALE / CHECKOUT
    # ==========================================

    def create_sale(
        self,
        sale: Sale,
        items: list[dict],
        payment: Optional[dict] = None,
    ) -> dict:
        """
        Complete a POS checkout.

        Item format:
        [
            {
                "variant_id": 1,
                "quantity": 2,
                "discount_amount": 0
            }
        ]

        Optional payment format:
        {
            "payment_method": "CASH",
            "amount": 5000,
            "reference_number": None,
            "notes": None
        }

        Returns:
            {
                "sale_id": int,
                "sale_number": str,
                "sale_item_ids": list[int],
                "payment_id": int | None
            }
        """

        if not isinstance(sale, Sale):
            raise TypeError("sale must be a Sale instance.")

        if not isinstance(items, list) or not items:
            raise ValueError("A sale must contain at least one item.")

        if sale.sale_status != "COMPLETED":
            raise ValueError(
                "New POS checkout sales must have COMPLETED status."
            )

        prepared_items = []
        seen_variants = set()

        # Validate cart input before starting the transaction.
        for item in items:

            if not isinstance(item, dict):
                raise TypeError(
                    "Each sale item must be a dictionary."
                )

            variant_id = item.get("variant_id")
            quantity = item.get("quantity")
            discount = item.get("discount_amount", 0)

            self._validate_positive_integer(
                variant_id, "Variant ID"
            )

            self._validate_positive_integer(
                quantity, "Quantity"
            )

            self._validate_non_negative_integer(
                discount, "Discount amount"
            )

            if variant_id in seen_variants:
                raise ValueError(
                    f"Duplicate variant in cart: {variant_id}. "
                    "Combine its quantities into one item."
                )

            seen_variants.add(variant_id)

            prepared_items.append({
                "variant_id": variant_id,
                "quantity": quantity,
                "discount_amount": discount,
            })

        if payment is not None and not isinstance(payment, dict):
            raise TypeError("payment must be a dictionary or None.")

        if payment is not None:
            self._validate_positive_integer(
                payment.get("amount"),
                "Payment amount"
            )

        try:
            with self.database.transaction() as connection:

                # ----------------------------------
                # 1. Validate sale number uniqueness
                # ----------------------------------

                existing_sale = connection.execute(
                    """
                    SELECT 1
                    FROM sales
                    WHERE sale_number = ?
                    LIMIT 1
                    """,
                    (sale.sale_number,)
                ).fetchone()

                if existing_sale:
                    raise ValueError(
                        f"Sale number already exists: {sale.sale_number}"
                    )

                # ----------------------------------
                # 2. Retrieve products and calculate
                # ----------------------------------

                sale_items = []
                calculated_subtotal = 0
                calculated_discount = 0

                for item in prepared_items:

                    row = connection.execute(
                        """
                        SELECT
                            pv.variant_id,
                            pv.sku,
                            pv.cost_price,
                            pv.selling_price,
                            p.product_name

                        FROM product_variants pv

                        INNER JOIN products p
                            ON pv.product_id = p.product_id

                        WHERE pv.variant_id = ?
                          AND pv.is_active = 1
                          AND p.is_active = 1
                        """,
                        (item["variant_id"],)
                    ).fetchone()

                    if row is None:
                        raise ValueError(
                            f"Product variant {item['variant_id']} "
                            "does not exist or is inactive."
                        )

                    quantity = item["quantity"]
                    unit_price = int(row["selling_price"])
                    unit_cost = int(row["cost_price"])
                    discount = item["discount_amount"]

                    gross_total = quantity * unit_price

                    if discount > gross_total:
                        raise ValueError(
                            f"Discount exceeds the gross amount "
                            f"for SKU {row['sku']}."
                        )

                    line_total = gross_total - discount

                    sale_item = SaleItem(
                        sale_id=1,  # Replaced after sale creation.
                        variant_id=row["variant_id"],
                        product_name=row["product_name"],
                        sku=row["sku"],
                        quantity=quantity,
                        unit_cost=unit_cost,
                        unit_price=unit_price,
                        discount_amount=discount,
                        line_total=line_total,
                    )

                    sale_items.append(sale_item)

                    calculated_subtotal += gross_total
                    calculated_discount += discount

                # ----------------------------------
                # 3. Verify sale totals
                # ----------------------------------

                if sale.subtotal != calculated_subtotal:
                    raise ValueError(
                        "Sale subtotal does not match the cart."
                    )

                if sale.discount_amount != calculated_discount:
                    raise ValueError(
                        "Sale discount does not match item discounts."
                    )

                expected_total = (
                    calculated_subtotal
                    - calculated_discount
                    + sale.tax_amount
                )

                if sale.total_amount != expected_total:
                    raise ValueError(
                        "Sale total does not match the calculated amount."
                    )

                # ----------------------------------
                # 4. Create sale header
                # ----------------------------------

                sale_id = self.sale_repository.create(
                    sale,
                    connection=connection
                )

                # ----------------------------------
                # 5. Create sale items and deduct stock
                # ----------------------------------

                sale_item_ids = []

                for sale_item in sale_items:

                    sale_item.sale_id = sale_id

                    sale_item_id = self.sale_item_repository.create(
                        sale_item,
                        connection=connection
                    )

                    sale_item_ids.append(sale_item_id)

                    variant_id = sale_item.variant_id
                    quantity = sale_item.quantity

                    # Atomically deduct stock.
                    cursor = connection.execute(
                        """
                        UPDATE inventory
                        SET quantity_on_hand = quantity_on_hand - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE variant_id = ?
                          AND quantity_on_hand >= ?
                        """,
                        (quantity, variant_id, quantity)
                    )

                    if cursor.rowcount == 0:
                        raise ValueError(
                            f"Insufficient stock for SKU "
                            f"{sale_item.sku}."
                        )

                    # Retrieve the updated balance.
                    stock_row = connection.execute(
                        """
                        SELECT quantity_on_hand
                        FROM inventory
                        WHERE variant_id = ?
                        """,
                        (variant_id,)
                    ).fetchone()

                    quantity_after = int(
                        stock_row["quantity_on_hand"]
                    )

                    # Record stock movement.
                    movement = InventoryTransaction(
                        variant_id=variant_id,
                        transaction_type="SALE",
                        quantity_change=-quantity,
                        quantity_after=quantity_after,
                        reference_type="SALE",
                        reference_id=sale_id,
                        notes=f"POS sale {sale.sale_number}",
                    )

                    self.transaction_repository.create(
                        movement,
                        connection=connection
                    )

                # ----------------------------------
                # 6. Record optional payment
                # ----------------------------------

                payment_id = None

                if payment is not None:

                    payment_amount = payment["amount"]

                    if payment_amount > sale.total_amount:
                        raise ValueError(
                            "Payment cannot exceed sale total."
                        )

                    payment_record = Payment(
                        sale_id=sale_id,
                        payment_method=payment.get("payment_method"),
                        amount=payment_amount,
                        payment_status="COMPLETED",
                        reference_number=payment.get(
                            "reference_number"
                        ),
                        notes=payment.get("notes"),
                    )

                    payment_id = self.payment_repository.create(
                        payment_record,
                        connection=connection
                    )

                return {
                    "sale_id": sale_id,
                    "sale_number": sale.sale_number,
                    "sale_item_ids": sale_item_ids,
                    "payment_id": payment_id,
                }

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to complete sale: {error}"
            ) from error

    # ==========================================
    # SALE RETRIEVAL
    # ==========================================

    def get_sale_details(self, sale_id: int) -> dict:
        """Retrieve a sale with its items and payment history."""

        if (
            not isinstance(sale_id, int)
            or isinstance(sale_id, bool)
            or sale_id <= 0
        ):
            raise ValueError("Sale ID must be a positive integer.")

        with closing(self.database.connect()) as connection:

            sale = connection.execute(
                """
                SELECT
                    s.*,
                    c.customer_name,
                    c.phone AS customer_phone,
                    u.full_name AS cashier_name

                FROM sales s

                LEFT JOIN customers c
                    ON s.customer_id = c.customer_id

                LEFT JOIN users u
                    ON s.cashier_user_id = u.user_id

                WHERE s.sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            if sale is None:
                raise ValueError("Sale does not exist.")

            item_rows = connection.execute(
                """
                SELECT
                    sale_item_id,
                    sale_id,
                    variant_id,
                    product_name,
                    sku,
                    quantity,
                    unit_cost,
                    unit_price,
                    discount_amount,
                    line_total,
                    created_at

                FROM sale_items
                WHERE sale_id = ?
                ORDER BY sale_item_id
                """,
                (sale_id,)
            ).fetchall()

            payment_rows = connection.execute(
                """
                SELECT *
                FROM payments
                WHERE sale_id = ?
                ORDER BY payment_id
                """,
                (sale_id,)
            ).fetchall()

            payment_summary = connection.execute(
                """
                SELECT
                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'COMPLETED'
                                THEN amount
                                ELSE 0
                            END
                        ), 0
                    ) AS paid_amount

                FROM payments
                WHERE sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            sale_data = dict(sale)
            items = [dict(row) for row in item_rows]
            payments = [dict(row) for row in payment_rows]

            paid_amount = int(payment_summary["paid_amount"])
            total_amount = int(sale_data["total_amount"])

            return {
                "sale": sale_data,
                "items": items,
                "payments": payments,
                "payment_summary": {
                    "total_amount": total_amount,
                    "paid_amount": paid_amount,
                    "outstanding_balance": total_amount - paid_amount,
                    "is_fully_paid": paid_amount == total_amount,
                }
            }

    # ==========================================
    # RETRIEVE BY RECEIPT NUMBER
    # ==========================================

    def get_sale_by_number(self, sale_number: str) -> dict:
        """Retrieve sale details using a receipt number."""

        if not isinstance(sale_number, str) or not sale_number.strip():
            raise ValueError("Sale number is required.")

        with closing(self.database.connect()) as connection:

            row = connection.execute(
                """
                SELECT sale_id
                FROM sales
                WHERE sale_number = ?
                """,
                (sale_number.strip(),)
            ).fetchone()

            if row is None:
                raise ValueError("Sale does not exist.")

            sale_id = row["sale_id"]

        return self.get_sale_details(sale_id)

    # ==========================================
    # RECEIPT DATA
    # ==========================================

    def get_receipt_data(self, sale_id: int) -> dict:
        """
        Prepare receipt information.

        This method returns data for the receipt UI or printer.
        It does not directly print anything.
        """

        details = self.get_sale_details(sale_id)

        sale = details["sale"]

        return {
            "receipt_number": sale["sale_number"],
            "sale_date": sale["created_at"],
            "sale_status": sale["sale_status"],

            "cashier": sale["cashier_name"],
            "customer": sale["customer_name"],
            "customer_phone": sale["customer_phone"],

            "items": details["items"],

            "subtotal": sale["subtotal"],
            "discount_amount": sale["discount_amount"],
            "tax_amount": sale["tax_amount"],
            "total_amount": sale["total_amount"],

            "payments": details["payments"],
            "paid_amount": details["payment_summary"]["paid_amount"],
            "outstanding_balance": (
                details["payment_summary"]["outstanding_balance"]
            ),

            "is_fully_paid": (
                details["payment_summary"]["is_fully_paid"]
            )
        }
