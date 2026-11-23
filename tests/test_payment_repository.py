
from uuid import uuid4

from src.core.database import Database
from src.models import Sale, Payment
from src.repositories import SaleRepository, PaymentRepository


def run_tests():

    database = Database()
    database.initialize()

    sale_repository = SaleRepository(database)
    payment_repository = PaymentRepository(database)

    suffix = uuid4().hex[:8]

    # ==========================================
    # CREATE A SALE FOR PAYMENT TESTS
    # ==========================================

    sale_id = sale_repository.create(
        Sale(
            sale_number=f"PAYMENT-TEST-{suffix}",
            subtotal=50000,
            discount_amount=0,
            tax_amount=0,
            total_amount=50000
        )
    )

    # ==========================================
    # CREATE PAYMENT
    # ==========================================

    payment_id = payment_repository.create(
        Payment(
            sale_id=sale_id,
            payment_method="CASH",
            amount=30000,
            reference_number=f"CASH-{suffix}",
            notes="Payment repository test"
        )
    )

    assert payment_id > 0
    print("Payment creation: PASSED")

    # ==========================================
    # RETRIEVE BY ID
    # ==========================================

    payment = payment_repository.get_by_id(payment_id)

    assert payment is not None
    assert payment.sale_id == sale_id
    assert payment.amount == 30000
    assert payment.payment_method == "CASH"

    print("Payment retrieval by ID: PASSED")

    # ==========================================
    # RETRIEVE BY SALE
    # ==========================================

    payments = payment_repository.get_by_sale(sale_id)

    assert len(payments) == 1
    assert payments[0].payment_id == payment_id

    print("Payment filtering by sale: PASSED")

    # ==========================================
    # RETRIEVE ALL
    # ==========================================

    all_payments = payment_repository.get_all()

    assert any(
        item.payment_id == payment_id
        for item in all_payments
    )

    print("All payments retrieval: PASSED")

    # ==========================================
    # FILTER BY METHOD
    # ==========================================

    cash_payments = payment_repository.get_by_method("CASH")

    assert any(
        item.payment_id == payment_id
        for item in cash_payments
    )

    print("Payment method filtering: PASSED")

    # ==========================================
    # FILTER BY STATUS
    # ==========================================

    completed_payments = payment_repository.get_by_status(
        "COMPLETED"
    )

    assert any(
        item.payment_id == payment_id
        for item in completed_payments
    )

    print("Payment status filtering: PASSED")

    # ==========================================
    # UPDATE STATUS
    # ==========================================

    assert payment_repository.update_status(
        payment_id,
        "REFUNDED"
    )

    updated_payment = payment_repository.get_by_id(payment_id)

    assert updated_payment.payment_status == "REFUNDED"

    print("Payment status update: PASSED")

    # ==========================================
    # COMPLETED PAYMENT TOTAL
    # ==========================================

    total = payment_repository.get_completed_total_by_sale(
        sale_id
    )

    assert total == 0

    # Create another completed payment.
    payment_repository.create(
        Payment(
            sale_id=sale_id,
            payment_method="CARD",
            amount=20000,
            reference_number=f"CARD-{suffix}"
        )
    )

    total = payment_repository.get_completed_total_by_sale(
        sale_id
    )

    assert total == 20000

    print("Completed payment total: PASSED")

    # ==========================================
    # EXISTENCE AND COUNT
    # ==========================================

    assert payment_repository.exists(payment_id)

    print("Payment existence check: PASSED")

    assert payment_repository.count_by_sale(sale_id) == 2

    print("Payment count: PASSED")

    # ==========================================
    # INVALID METHOD
    # ==========================================

    try:
        payment_repository.get_by_method("BITCOIN")

    except ValueError:
        print("Invalid payment method prevention: PASSED")

    else:
        raise AssertionError("Invalid payment method was accepted.")

    # ==========================================
    # INVALID STATUS
    # ==========================================

    try:
        payment_repository.update_status(
            payment_id,
            "INVALID"
        )

    except ValueError:
        print("Invalid payment status prevention: PASSED")

    else:
        raise AssertionError("Invalid payment status was accepted.")

    print("\nAll PaymentRepository tests passed!")


if __name__ == "__main__":
    run_tests()
