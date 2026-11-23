
from uuid import uuid4

from src.core.database import Database
from src.models import Sale, Payment
from src.repositories import SaleRepository, PaymentRepository
from src.services import PaymentService


def run_tests():

    database = Database()
    database.initialize()

    sale_repository = SaleRepository(database)
    payment_repository = PaymentRepository(database)
    payment_service = PaymentService(database)

    suffix = uuid4().hex[:8]

    # ==========================================
    # CREATE TEST SALE
    # ==========================================

    sale_id = sale_repository.create(
        Sale(
            sale_number=f"PAY-SERVICE-{suffix}",
            subtotal=50000,
            discount_amount=0,
            tax_amount=0,
            total_amount=50000
        )
    )

    print("Test sale creation: PASSED")

    # ==========================================
    # INITIAL PAYMENT SUMMARY
    # ==========================================

    summary = payment_service.get_payment_summary(sale_id)

    assert summary["total_amount"] == 50000
    assert summary["paid_amount"] == 0
    assert summary["outstanding_balance"] == 50000
    assert summary["is_unpaid"] is True

    print("Initial payment summary: PASSED")

    # ==========================================
    # FIRST SPLIT PAYMENT
    # ==========================================

    first_payment_id = payment_service.record_payment(
        Payment(
            sale_id=sale_id,
            payment_method="CASH",
            amount=20000
        )
    )

    assert first_payment_id > 0

    summary = payment_service.get_payment_summary(sale_id)

    assert summary["paid_amount"] == 20000
    assert summary["outstanding_balance"] == 30000
    assert summary["is_partially_paid"] is True

    print("First split payment: PASSED")

    # ==========================================
    # SECOND SPLIT PAYMENT
    # ==========================================

    second_payment_id = payment_service.record_payment(
        Payment(
            sale_id=sale_id,
            payment_method="CARD",
            amount=30000,
            reference_number=f"CARD-{suffix}"
        )
    )

    assert second_payment_id > 0

    summary = payment_service.get_payment_summary(sale_id)

    assert summary["paid_amount"] == 50000
    assert summary["outstanding_balance"] == 0
    assert summary["is_fully_paid"] is True

    print("Second split payment: PASSED")
    print("Full payment calculation: PASSED")

    # ==========================================
    # OUTSTANDING BALANCE
    # ==========================================

    assert payment_service.get_outstanding_balance(sale_id) == 0
    assert payment_service.is_fully_paid(sale_id) is True

    print("Outstanding balance calculation: PASSED")

    # ==========================================
    # OVERPAYMENT PREVENTION
    # ==========================================

    try:
        payment_service.record_payment(
            Payment(
                sale_id=sale_id,
                payment_method="CASH",
                amount=1000
            )
        )

    except ValueError:
        print("Overpayment prevention: PASSED")

    else:
        raise AssertionError("Overpayment was accepted.")

    # Verify that the rejected payment was not saved.
    assert payment_repository.count_by_sale(sale_id) == 2

    print("Overpayment rollback verification: PASSED")

    # ==========================================
    # FAILED PAYMENT REJECTION
    # ==========================================

    try:
        payment_service.record_payment(
            Payment(
                sale_id=sale_id,
                payment_method="CARD",
                amount=1000,
                payment_status="FAILED"
            )
        )

    except ValueError:
        print("Non-completed payment rejection: PASSED")

    else:
        raise AssertionError(
            "A failed payment was accepted as a completed payment."
        )

    # ==========================================
    # INVALID SALE
    # ==========================================

    try:
        payment_service.record_payment(
            Payment(
                sale_id=999999999,
                payment_method="CASH",
                amount=1000
            )
        )

    except ValueError:
        print("Invalid sale prevention: PASSED")

    else:
        raise AssertionError("Payment for an invalid sale was accepted.")

    print("\nAll PaymentService tests passed!")


if __name__ == "__main__":
    run_tests()
