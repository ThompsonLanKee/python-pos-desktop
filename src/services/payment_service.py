
from contextlib import closing

from src.core.database import Database
from src.models import Payment
from src.repositories import PaymentRepository


class PaymentService:
    """
    Handles payment business rules.

    Supports:
        - Cash, card, mobile, and bank-transfer payments
        - Split payments
        - Outstanding balance calculation
        - Overpayment prevention
        - Rejection of payments for voided/refunded sales

    Only successful payments reduce the outstanding balance.
    """

    def __init__(self, database: Database):
        self.database = database
        self.payment_repository = PaymentRepository(database)

    # ==========================================
    # RECORD COMPLETED PAYMENT
    # ==========================================

    def record_payment(self, payment: Payment) -> int:
        """
        Record a successful payment.

        The payment is inserted only if:
            - The sale exists.
            - The sale is not voided or refunded.
            - The payment does not exceed the outstanding balance.

        Returns:
            The new payment ID.
        """

        if not isinstance(payment, Payment):
            raise TypeError("payment must be a Payment instance.")

        if payment.payment_status != "COMPLETED":
            raise ValueError(
                "record_payment only accepts completed payments."
            )

        try:
            with self.database.transaction() as connection:

                # 1. Retrieve and validate the sale.
                sale = connection.execute(
                    """
                    SELECT
                        sale_id,
                        total_amount,
                        sale_status
                    FROM sales
                    WHERE sale_id = ?
                    """,
                    (payment.sale_id,)
                ).fetchone()

                if sale is None:
                    raise ValueError("Sale does not exist.")

                if sale["sale_status"] in ("VOIDED", "REFUNDED"):
                    raise ValueError(
                        "Cannot accept payment for a voided or refunded sale."
                    )

                # 2. Calculate completed payments.
                payment_row = connection.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS paid_amount
                    FROM payments
                    WHERE sale_id = ?
                      AND payment_status = 'COMPLETED'
                    """,
                    (payment.sale_id,)
                ).fetchone()

                paid_amount = int(payment_row["paid_amount"])
                total_amount = int(sale["total_amount"])

                outstanding_balance = total_amount - paid_amount

                # 3. Prevent overpayment.
                if payment.amount > outstanding_balance:
                    raise ValueError(
                        "Payment exceeds outstanding balance. "
                        f"Outstanding: {outstanding_balance}, "
                        f"attempted: {payment.amount}."
                    )

                if outstanding_balance <= 0:
                    raise ValueError(
                        "This sale has already been fully paid."
                    )

                # 4. Insert payment using the same transaction.
                payment_id = self.payment_repository.create(
                    payment,
                    connection=connection
                )

                return payment_id

        except ValueError:
            raise

    # ==========================================
    # PAYMENT SUMMARY
    # ==========================================

    def get_payment_summary(self, sale_id: int) -> dict:
        """
        Return gross payment totals, refunds, and outstanding balance.
        """

        if not isinstance(sale_id, int) or isinstance(sale_id, bool):
            raise ValueError("Sale ID must be an integer.")

        if sale_id <= 0:
            raise ValueError("Sale ID must be positive.")

        with closing(self.database.connect()) as connection:

            sale = connection.execute(
                """
                SELECT
                    sale_id,
                    sale_number,
                    total_amount,
                    sale_status
                FROM sales
                WHERE sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            if sale is None:
                raise ValueError("Sale does not exist.")

            payment_totals = connection.execute(
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
                    ) AS gross_paid_amount,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'FAILED'
                                THEN amount
                                ELSE 0
                            END
                        ), 0
                    ) AS failed_amount

                FROM payments
                WHERE sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            refund_row = connection.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS refunded_amount
                FROM refunds
                WHERE sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            total_amount = int(sale["total_amount"])
            gross_paid_amount = int(
                payment_totals["gross_paid_amount"]
            )
            refunded_amount = int(refund_row["refunded_amount"])

            paid_amount = gross_paid_amount - refunded_amount

            return {
                "sale_id": sale["sale_id"],
                "sale_number": sale["sale_number"],
                "sale_status": sale["sale_status"],
                "total_amount": total_amount,
                "gross_paid_amount": gross_paid_amount,
                "paid_amount": paid_amount,
                "outstanding_balance": total_amount - gross_paid_amount,
                "failed_amount": int(payment_totals["failed_amount"]),
                "refunded_amount": refunded_amount,
                "net_paid_amount": paid_amount,
                "is_fully_paid": (
                    paid_amount == total_amount
                    and sale["sale_status"] != "REFUNDED"
                ),
                "is_partially_paid": 0 < paid_amount < total_amount,
                "is_unpaid": paid_amount == 0,
            }

    # ==========================================
    # OUTSTANDING BALANCE
    # ==========================================

    def get_outstanding_balance(self, sale_id: int) -> int:
        """Return the remaining amount due for a sale."""

        summary = self.get_payment_summary(sale_id)

        return summary["outstanding_balance"]

    # ==========================================
    # PAYMENT COMPLETION CHECK
    # ==========================================

    def is_fully_paid(self, sale_id: int) -> bool:
        """Check whether completed payments equal the sale total."""

        summary = self.get_payment_summary(sale_id)

        return summary["is_fully_paid"]
