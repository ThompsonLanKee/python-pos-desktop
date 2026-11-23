
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
        """
        Record a refund against an original completed payment.

        Multiple partial refunds are supported, but their
        combined amount cannot exceed the original payment.
        """

        if not isinstance(refund, Refund):
            raise TypeError("refund must be a Refund instance.")

        try:
            with self.database.transaction() as connection:

                # 1. Retrieve original payment and sale.
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

                # 2. Calculate previous refunds for this payment.
                previous_refunds = connection.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS refunded_amount
                    FROM refunds
                    WHERE payment_id = ?
                    """,
                    (refund.payment_id,)
                ).fetchone()

                already_refunded = int(
                    previous_refunds["refunded_amount"]
                )

                refundable_balance = (
                    int(payment["amount"]) - already_refunded
                )

                if refund.amount > refundable_balance:
                    raise ValueError(
                        "Refund exceeds the refundable payment balance. "
                        f"Remaining refundable amount: "
                        f"{refundable_balance}."
                    )

                if refundable_balance <= 0:
                    raise ValueError(
                        "This payment has already been fully refunded."
                    )

                # 3. Insert refund.
                refund_id = self.refund_repository.create(
                    refund,
                    connection=connection
                )

                # 4. Calculate total paid and refunded for this sale.
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

                # 5. Mark sale refunded only when the full sale
                # amount has been paid and subsequently refunded.
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
