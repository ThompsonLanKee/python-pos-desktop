
from uuid import uuid4

from src.core.database import Database
from src.models import (
    Category,
    Product,
    ProductVariant,
    Sale,
    Refund,
)
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
    RefundRepository,
)
from src.services.sale_service import SaleService
from src.services.sales_return_service import SalesReturnService
from src.services.refund_service import RefundService


class RefundServiceTest:

    def __init__(self):
        self.database = Database()
        self.database.initialize()

        self.category_repository = CategoryRepository(self.database)
        self.product_repository = ProductRepository(self.database)
        self.variant_repository = ProductVariantRepository(self.database)
        self.inventory_repository = InventoryRepository(self.database)

        self.refund_repository = RefundRepository(self.database)

        self.sale_service = SaleService(self.database)
        self.return_service = SalesReturnService(self.database)
        self.refund_service = RefundService(self.database)

        self.suffix = uuid4().hex[:10]
        self.variant_id = self._create_product()

    # --------------------------------------------------
    # TEST DATA
    # --------------------------------------------------

    def _create_product(self):
        category_id = self.category_repository.create(
            Category(
                category_name=f"Refund Category {self.suffix}"
            )
        )

        product_id = self.product_repository.create(
            Product(
                product_name=f"Refund Product {self.suffix}",
                category_id=category_id,
                description="Product for refund service tests",
            )
        )

        variant_id = self.variant_repository.create(
            ProductVariant(
                product_id=product_id,
                color_id=None,
                size_id=None,
                sku=f"REFUND-{self.suffix}",
                barcode=None,
                cost_price=500,
                selling_price=1000,
            )
        )

        self.inventory_repository.create(variant_id)
        self.inventory_repository.adjust_quantity(variant_id, 30)

        return variant_id

    def _create_sale(self, quantity=3, payment_amount=None):
        sale_number = f"REFUND-SALE-{uuid4().hex[:10]}"
        total_amount = quantity * 1000

        if payment_amount is None:
            payment_amount = total_amount

        sale = Sale(
            sale_number=sale_number,
            subtotal=total_amount,
            discount_amount=0,
            tax_amount=0,
            total_amount=total_amount,
        )

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_id,
                    "quantity": quantity,
                }
            ],
            payment={
                "payment_method": "CASH",
                "amount": payment_amount,
            },
        )

        return {
            "sale_id": result["sale_id"],
            "sale_item_id": result["sale_item_ids"][0],
            "sale_number": sale_number,
            "payment_id": result["payment_id"],
            "total_amount": total_amount,
            "quantity": quantity,
            "payment_amount": payment_amount,
        }

    def _create_return(self, sale_data, quantity):
        return self.return_service.create_return(
            return_number=f"REFUND-RETURN-{uuid4().hex[:10]}",
            sale_id=sale_data["sale_id"],
            items=[
                {
                    "sale_item_id": sale_data["sale_item_id"],
                    "quantity": quantity,
                    "restock": True,
                    "condition": "GOOD",
                }
            ],
            reason="Refund service test",
        )

    def _record_refund(
        self,
        sale_data,
        return_data,
        amount,
        payment_id=None,
    ):
        return self.refund_service.record_refund(
            Refund(
                payment_id=(
                    payment_id
                    if payment_id is not None
                    else sale_data["payment_id"]
                ),
                sale_id=sale_data["sale_id"],
                return_id=return_data["return_id"],
                amount=amount,
                reference_number=f"REF-{uuid4().hex[:10]}",
                notes="Refund service test",
            )
        )

    def _refund_count(self, return_id):
        return len(
            self.refund_repository.get_by_return(return_id)
        )

    # --------------------------------------------------
    # TEST 1: SUCCESSFUL PARTIAL REFUND
    # --------------------------------------------------

    def test_partial_refund(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        refund_id = self._record_refund(
            sale_data,
            return_data,
            amount=500,
        )

        assert refund_id > 0

        refunds = self.refund_repository.get_by_return(
            return_data["return_id"]
        )

        assert len(refunds) == 1
        assert refunds[0].amount == 500

        print("Successful partial refund: PASSED")

    # --------------------------------------------------
    # TEST 2: MULTIPLE PARTIAL REFUNDS
    # --------------------------------------------------

    def test_multiple_partial_refunds(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        first_id = self._record_refund(
            sale_data,
            return_data,
            amount=400,
        )

        second_id = self._record_refund(
            sale_data,
            return_data,
            amount=600,
        )

        assert first_id > 0
        assert second_id > 0

        total_refunded = self.refund_repository.get_total_by_return(
            return_data["return_id"]
        )

        assert total_refunded == 1000

        print("Multiple partial refunds: PASSED")

    # --------------------------------------------------
    # TEST 3: FULL SALE REFUND
    # --------------------------------------------------

    def test_full_sale_refund(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=2)

        self._record_refund(
            sale_data,
            return_data,
            amount=2000,
        )

        summary = self.refund_service.get_refund_summary(
            sale_data["sale_id"]
        )

        assert summary["paid_amount"] == 2000
        assert summary["refunded_amount"] == 2000
        assert summary["net_paid_amount"] == 0
        assert summary["is_fully_refunded"] is True
        assert summary["sale_status"] == "REFUNDED"

        print("Full sale refund: PASSED")

    # --------------------------------------------------
    # TEST 4: REFUND EXCEEDS RETURN AMOUNT
    # --------------------------------------------------

    def test_return_amount_limit(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        try:
            self._record_refund(
                sale_data,
                return_data,
                amount=1500,
            )
        except ValueError:
            assert self._refund_count(
                return_data["return_id"]
            ) == 0

            print("Return refund limit: PASSED")
        else:
            raise AssertionError(
                "Refund exceeding the return amount was accepted."
            )

    # --------------------------------------------------
    # TEST 5: REFUND EXCEEDS PAYMENT BALANCE
    # --------------------------------------------------

    def test_payment_amount_limit(self):
        sale_data = self._create_sale(
            quantity=3,
            payment_amount=2000,
        )

        return_data = self._create_return(
            sale_data,
            quantity=3,
        )

        try:
            self._record_refund(
                sale_data,
                return_data,
                amount=2500,
            )
        except ValueError:
            assert self._refund_count(
                return_data["return_id"]
            ) == 0

            print("Original payment refund limit: PASSED")
        else:
            raise AssertionError(
                "Refund exceeding the original payment was accepted."
            )

    # --------------------------------------------------
    # TEST 6: REFUND CANNOT EXCEED REMAINING BALANCE
    # --------------------------------------------------

    def test_remaining_payment_balance(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=2)

        self._record_refund(
            sale_data,
            return_data,
            amount=1500,
        )

        try:
            self._record_refund(
                sale_data,
                return_data,
                amount=600,
            )
        except ValueError:
            total = self.refund_repository.get_total_by_payment(
                sale_data["payment_id"]
            )

            assert total == 1500

            print("Remaining payment balance prevention: PASSED")
        else:
            raise AssertionError(
                "Refund exceeding the remaining payment balance was accepted."
            )

    # --------------------------------------------------
    # TEST 7: RETURN MUST BELONG TO THE SAME SALE
    # --------------------------------------------------

    def test_return_sale_mismatch(self):
        first_sale = self._create_sale(quantity=2)
        second_sale = self._create_sale(quantity=2)

        second_return = self._create_return(
            second_sale,
            quantity=1,
        )

        try:
            self._record_refund(
                first_sale,
                second_return,
                amount=500,
            )
        except ValueError:
            assert self._refund_count(
                second_return["return_id"]
            ) == 0

            print("Return and sale relationship validation: PASSED")
        else:
            raise AssertionError(
                "A return belonging to another sale was accepted."
            )

    # --------------------------------------------------
    # TEST 8: INVALID RETURN ID
    # --------------------------------------------------

    def test_invalid_return(self):
        sale_data = self._create_sale(quantity=2)

        try:
            self.refund_service.record_refund(
                Refund(
                    payment_id=sale_data["payment_id"],
                    sale_id=sale_data["sale_id"],
                    return_id=999999999,
                    amount=500,
                )
            )
        except ValueError:
            print("Invalid return prevention: PASSED")
        else:
            raise AssertionError(
                "Refund for a nonexistent return was accepted."
            )

    # --------------------------------------------------
    # TEST 9: NON-COMPLETED PAYMENT
    # --------------------------------------------------

    def test_non_completed_payment(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO payments (
                    sale_id,
                    payment_method,
                    amount,
                    payment_status,
                    reference_number
                )
                VALUES (?, 'CASH', ?, 'FAILED', ?)
                """,
                (
                    sale_data["sale_id"],
                    1000,
                    f"FAILED-{uuid4().hex[:10]}",
                ),
            )

            failed_payment_id = cursor.lastrowid

        try:
            self._record_refund(
                sale_data,
                return_data,
                amount=500,
                payment_id=failed_payment_id,
            )
        except ValueError:
            print("Non-completed payment rejection: PASSED")
        else:
            raise AssertionError(
                "A refund against a failed payment was accepted."
            )

    # --------------------------------------------------
    # TEST 10: REFUND SUMMARY
    # --------------------------------------------------

    def test_refund_summary(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        self._record_refund(
            sale_data,
            return_data,
            amount=400,
        )

        summary = self.refund_service.get_refund_summary(
            sale_data["sale_id"]
        )

        assert summary["sale_id"] == sale_data["sale_id"]
        assert summary["paid_amount"] == 2000
        assert summary["refunded_amount"] == 400
        assert summary["net_paid_amount"] == 1600
        assert summary["refundable_amount"] == 1600
        assert summary["outstanding_balance"] == 0
        assert summary["is_fully_refunded"] is False

        print("Refund summary calculation: PASSED")

    # --------------------------------------------------
    # TEST 11: TRANSACTION ROLLBACK
    # --------------------------------------------------

    def test_refund_transaction_rollback(self):
        sale_data = self._create_sale(quantity=2)
        return_data = self._create_return(sale_data, quantity=1)

        refunds_before = self._refund_count(
            return_data["return_id"]
        )

        try:
            self._record_refund(
                sale_data,
                return_data,
                amount=1500,
            )
        except ValueError:
            refunds_after = self._refund_count(
                return_data["return_id"]
            )

            assert refunds_after == refunds_before

            print("Refund transaction rollback: PASSED")
        else:
            raise AssertionError(
                "Invalid refund unexpectedly succeeded."
            )

    # --------------------------------------------------
    # RUN ALL TESTS
    # --------------------------------------------------

    def run_tests(self):
        print("\nStarting RefundService tests...\n")

        self.test_partial_refund()
        self.test_multiple_partial_refunds()
        self.test_full_sale_refund()
        self.test_return_amount_limit()
        self.test_payment_amount_limit()
        self.test_remaining_payment_balance()
        self.test_return_sale_mismatch()
        self.test_invalid_return()
        self.test_non_completed_payment()
        self.test_refund_summary()
        self.test_refund_transaction_rollback()

        print("\nAll RefundService tests passed!")


def run_tests():
    test = RefundServiceTest()
    test.run_tests()


if __name__ == "__main__":
    run_tests()
