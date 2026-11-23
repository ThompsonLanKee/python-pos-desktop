
from uuid import uuid4

from src.core.database import Database
from src.models import (
    Category,
    Product,
    ProductVariant,
    Sale,
    Payment,
    Refund,
)
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
    PaymentRepository,
    SaleRepository,
    RefundRepository,
)
from src.services.sale_service import SaleService
from src.services.refund_service import RefundService
from src.services.payment_service import PaymentService


def run_tests():

    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    product_repo = ProductRepository(database)
    variant_repo = ProductVariantRepository(database)
    inventory_repo = InventoryRepository(database)
    payment_repo = PaymentRepository(database)
    sale_repo = SaleRepository(database)
    refund_repo = RefundRepository(database)

    sale_service = SaleService(database)
    refund_service = RefundService(database)
    payment_service = PaymentService(database)

    suffix = uuid4().hex[:10]

    print("\nStarting RefundService tests...\n")

    # 1. Prepare product and inventory.
    category_id = category_repo.create(
        Category(category_name=f"Refund Category {suffix}")
    )

    product_id = product_repo.create(
        Product(
            product_name=f"Refund Product {suffix}",
            category_id=category_id
        )
    )

    variant_id = variant_repo.create(
        ProductVariant(
            product_id=product_id,
            color_id=None,
            size_id=None,
            sku=f"REFUND-{suffix}",
            barcode=None,
            cost_price=500,
            selling_price=1000
        )
    )

    inventory_repo.create(variant_id)
    inventory_repo.adjust_quantity(variant_id, 10)

    # 2. Create a sale.
    sale_number = f"REFUND-SALE-{suffix}"

    sale = Sale(
        sale_number=sale_number,
        subtotal=2000,
        discount_amount=0,
        tax_amount=0,
        total_amount=2000
    )

    result = sale_service.create_sale(
        sale=sale,
        items=[
            {
                "variant_id": variant_id,
                "quantity": 2
            }
        ]
    )

    sale_id = result["sale_id"]

    print("Sale creation: PASSED")

    # 3. Record original completed payment.
    payment_id = payment_repo.create(
        Payment(
            sale_id=sale_id,
            payment_method="CASH",
            amount=2000
        )
    )

    payment_repo.create(
        Payment(
            sale_id=sale_id,
            payment_method="CARD",
            amount=100,
            payment_status="FAILED"
        )
    )

    print("Original payment creation: PASSED")

    # 4. First partial refund.
    first_refund_id = refund_service.record_refund(
        Refund(
            payment_id=payment_id,
            sale_id=sale_id,
            amount=600,
            notes="First partial refund"
        )
    )

    assert first_refund_id > 0

    print("First partial refund: PASSED")

    # 5. Second partial refund.
    second_refund_id = refund_service.record_refund(
        Refund(
            payment_id=payment_id,
            sale_id=sale_id,
            amount=400,
            notes="Second partial refund"
        )
    )

    assert second_refund_id > first_refund_id

    print("Second partial refund: PASSED")

    # 6. Prevent over-refunding.
    try:
        refund_service.record_refund(
            Refund(
                payment_id=payment_id,
                sale_id=sale_id,
                amount=1001
            )
        )

    except ValueError:
        print("Over-refund prevention: PASSED")

    else:
        raise AssertionError("Over-refund was accepted.")

    # 7. Verify refund summary.
    summary = refund_service.get_refund_summary(sale_id)

    assert summary["paid_amount"] == 2000
    assert summary["refunded_amount"] == 1000
    assert summary["net_paid_amount"] == 1000
    assert summary["refundable_amount"] == 1000
    assert summary["is_fully_refunded"] is False

    payment_summary = payment_service.get_payment_summary(sale_id)
    assert payment_summary["gross_paid_amount"] == 2000
    assert payment_summary["paid_amount"] == 1000
    assert payment_summary["net_paid_amount"] == 1000
    assert payment_summary["outstanding_balance"] == 0
    assert payment_summary["failed_amount"] == 100
    assert payment_summary["refunded_amount"] == 1000
    assert payment_summary["is_partially_paid"] is True

    print("Partial refund summary: PASSED")
    print("Refund-adjusted payment summary: PASSED")

    # 8. Verify original payment remains completed.
    original_payment = payment_repo.get_by_id(payment_id)

    assert original_payment.payment_status == "COMPLETED"
    assert original_payment.amount == 2000

    print("Original payment preservation: PASSED")

    # 9. Refund remaining amount.
    refund_service.record_refund(
        Refund(
            payment_id=payment_id,
            sale_id=sale_id,
            amount=1000,
            notes="Final refund"
        )
    )

    final_summary = refund_service.get_refund_summary(sale_id)

    assert final_summary["refunded_amount"] == 2000
    assert final_summary["net_paid_amount"] == 0
    assert final_summary["is_fully_refunded"] is True

    payment_summary = payment_service.get_payment_summary(sale_id)
    assert payment_summary["gross_paid_amount"] == 2000
    assert payment_summary["paid_amount"] == 0
    assert payment_summary["refunded_amount"] == 2000
    assert payment_summary["is_fully_paid"] is False
    assert payment_summary["is_unpaid"] is True

    print("Full refund completion: PASSED")

    # 10. Verify sale status.
    updated_sale = sale_repo.get_by_id(sale_id)

    assert updated_sale.sale_status == "REFUNDED"

    print("Sale status update: PASSED")

    # 11. Verify refund history.
    refunds = refund_repo.get_by_payment(payment_id)

    assert len(refunds) == 3
    assert sum(refund.amount for refund in refunds) == 2000

    print("Refund history retrieval: PASSED")

    # 12. Prevent further refunds.
    try:
        refund_service.record_refund(
            Refund(
                payment_id=payment_id,
                sale_id=sale_id,
                amount=1
            )
        )

    except ValueError:
        print("Refund after full refund prevention: PASSED")

    else:
        raise AssertionError(
            "Refund after full refund was accepted."
        )

    print("\nAll RefundService tests passed!")


if __name__ == "__main__":
    run_tests()
