
import sqlite3
from contextlib import closing

from src.core.database import Database
from src.models import Refund
from src.repositories import RefundRepository


class RefundService:
    """Handles full and partial sale payment refunds."""

    def __init__(self, database: Database):

        self.database = database
        self.refund_repository = RefundRepository(database)

    # ==========================================
    # RECORD REFUND
    # ==========================================

    def record_refund(self, refund: Refund) -> int:
        """Record a refund linked to a completed physical sales return."""

        if not isinstance(refund, Refund):
            raise TypeError("refund must be a Refund instance.")

        if refund.return_id is None:
            raise ValueError("A sales return ID is required.")

        try:
            with self.database.transaction() as connection:

                # 1. Verify that the return belongs to this sale.
                sales_return = connection.execute(
                    """
                    SELECT
                        return_id,
                        sale_id,
                        return_status,
                        total_refund_amount
                    FROM sales_returns
                    WHERE return_id = ?
                      AND sale_id = ?
                    """,
                    (refund.return_id, refund.sale_id)
                ).fetchone()

                if sales_return is None:
                    raise ValueError(
                        "Sales return does not exist for this sale."
                    )

                if sales_return["return_status"] != "COMPLETED":
                    raise ValueError(
                        "Only completed sales returns can be refunded."
                    )

                return_amount = int(
                    sales_return["total_refund_amount"]
                )

                if return_amount <= 0:
                    raise ValueError(
                        "This sales return has no refundable amount."
                    )

                # 2. Verify original payment and sale.
                payment = connection.execute(
                    """
                    SELECT
                        p.payment_id,
                        p.sale_id,
                        p.amount,
                        p.payment_status,
                        s.total_amount,
                        s.sale_status
                    FROM payments p
                    INNER JOIN sales s
                        ON p.sale_id = s.sale_id
                    WHERE p.payment_id = ?
                      AND p.sale_id = ?
                    """,
                    (refund.payment_id, refund.sale_id)
                ).fetchone()

                if payment is None:
                    raise ValueError(
                        "Payment does not exist for this sale."
                    )

                if payment["payment_status"] != "COMPLETED":
                    raise ValueError(
                        "Only completed payments can be refunded."
                    )

                if payment["sale_status"] in ("VOIDED", "REFUNDED"):
                    raise ValueError(
                        "Cannot refund a voided or fully refunded sale."
                    )

                # 3. Check remaining refundable amount for this return.
                already_refunded_for_return = int(
                    connection.execute(
                        """
                        SELECT COALESCE(SUM(amount), 0)
                            AS refunded_amount
                        FROM refunds
                        WHERE return_id = ?
                        """,
                        (refund.return_id,)
                    ).fetchone()["refunded_amount"]
                )

                remaining_return_amount = (
                    return_amount - already_refunded_for_return
                )

                if refund.amount > remaining_return_amount:
                    raise ValueError(
                        "Refund exceeds the remaining refundable "
                        f"amount for this return: "
                        f"{remaining_return_amount}."
                    )

                # 4. Check remaining refundable amount for payment.
                already_refunded_for_payment = int(
                    connection.execute(
                        """
                        SELECT COALESCE(SUM(amount), 0)
                            AS refunded_amount
                        FROM refunds
                        WHERE payment_id = ?
                        """,
                        (refund.payment_id,)
                    ).fetchone()["refunded_amount"]
                )

                remaining_payment_amount = (
                    int(payment["amount"])
                    - already_refunded_for_payment
                )

                if refund.amount > remaining_payment_amount:
                    raise ValueError(
                        "Refund exceeds the remaining refundable "
                        f"payment balance: {remaining_payment_amount}."
                    )

                # 5. Insert refund within the same transaction.
                refund_id = self.refund_repository.create(
                    refund,
                    connection=connection
                )

                # 6. Calculate totals for the entire sale.
                totals = connection.execute(
                    """
                    SELECT
                        (
                            SELECT COALESCE(SUM(amount), 0)
                            FROM payments
                            WHERE sale_id = ?
                              AND payment_status = 'COMPLETED'
                        ) AS paid_amount,

                        (
                            SELECT COALESCE(SUM(amount), 0)
                            FROM refunds
                            WHERE sale_id = ?
                        ) AS refunded_amount
                    """,
                    (refund.sale_id, refund.sale_id)
                ).fetchone()

                paid_amount = int(totals["paid_amount"])
                refunded_amount = int(totals["refunded_amount"])

                # 7. Mark sale fully refunded only when all paid
                # amounts have been refunded.
                if (
                    paid_amount == int(payment["total_amount"])
                    and refunded_amount == int(payment["total_amount"])
                ):
                    connection.execute(
                        """
                        UPDATE sales
                        SET sale_status = 'REFUNDED',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE sale_id = ?
                        """,
                        (refund.sale_id,)
                    )

                return refund_id

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to record refund: {error}"
            ) from error

    # ==========================================
    # REFUND SUMMARY
    # ==========================================

    def get_refund_summary(self, sale_id: int) -> dict:
        """Return payment and refund totals for a sale."""

        if (
            not isinstance(sale_id, int)
            or isinstance(sale_id, bool)
            or sale_id <= 0
        ):
            raise ValueError("Sale ID must be a positive integer.")

        with closing(self.database.connect()) as connection:

            sale = connection.execute(
                """
                SELECT sale_id, sale_number, total_amount, sale_status
                FROM sales
                WHERE sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            if sale is None:
                raise ValueError("Sale does not exist.")

            totals = connection.execute(
                """
                SELECT
                    (
                        SELECT COALESCE(SUM(amount), 0)
                        FROM payments
                        WHERE sale_id = ?
                          AND payment_status = 'COMPLETED'
                    ) AS paid_amount,

                    (
                        SELECT COALESCE(SUM(amount), 0)
                        FROM refunds
                        WHERE sale_id = ?
                    ) AS refunded_amount
                """,
                (sale_id, sale_id)
            ).fetchone()

            paid_amount = int(totals["paid_amount"])
            refunded_amount = int(totals["refunded_amount"])

            return {
                "sale_id": sale["sale_id"],
                "sale_number": sale["sale_number"],
                "sale_status": sale["sale_status"],
                "total_amount": int(sale["total_amount"]),
                "paid_amount": paid_amount,
                "refunded_amount": refunded_amount,
                "net_paid_amount": paid_amount - refunded_amount,
                "refundable_amount": paid_amount - refunded_amount,
                "outstanding_balance": (
                    int(sale["total_amount"]) - paid_amount
                ),
                "is_fully_refunded": (
                    paid_amount == int(sale["total_amount"])
                    and refunded_amount == int(sale["total_amount"])
                )
            }
