
from uuid import uuid4

from src.core.database import Database
from src.models import (
    Category,
    Product,
    ProductVariant,
    Sale,
)
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
    SaleRepository,
    SaleItemRepository,
    InventoryTransactionRepository,
)
from src.services.sale_service import SaleService


class SaleServiceTest:
    def __init__(self):
        self.database = Database()
        self.database.initialize()

        self.category_repository = CategoryRepository(self.database)
        self.product_repository = ProductRepository(self.database)
        self.variant_repository = ProductVariantRepository(self.database)
        self.inventory_repository = InventoryRepository(self.database)

        self.sale_repository = SaleRepository(self.database)
        self.sale_item_repository = SaleItemRepository(self.database)
        self.transaction_repository = InventoryTransactionRepository(
            self.database
        )

        self.sale_service = SaleService(self.database)

        self.suffix = uuid4().hex[:10]

        self.variant_1 = None
        self.variant_2 = None

        self._create_test_products()

    # ==========================================
    # TEST DATA
    # ==========================================

    def _create_test_products(self):
        category_id = self.category_repository.create(
            Category(
                category_name=f"Sale Test Category {self.suffix}"
            )
        )

        product_id = self.product_repository.create(
            Product(
                product_name=f"Sale Test Product {self.suffix}",
                category_id=category_id,
                description="Product for sale service tests",
            )
        )

        self.variant_1 = self._create_variant(
            product_id=product_id,
            sku=f"SALE-TEST-A-{self.suffix}",
            selling_price=1000,
            cost_price=500,
            initial_stock=10,
        )

        self.variant_2 = self._create_variant(
            product_id=product_id,
            sku=f"SALE-TEST-B-{self.suffix}",
            selling_price=2000,
            cost_price=1000,
            initial_stock=5,
        )

    def _create_variant(
        self,
        product_id,
        sku,
        selling_price,
        cost_price,
        initial_stock,
    ):
        variant_id = self.variant_repository.create(
            ProductVariant(
                product_id=product_id,
                color_id=None,
                size_id=None,
                sku=sku,
                barcode=None,
                cost_price=cost_price,
                selling_price=selling_price,
            )
        )

        self.inventory_repository.create(variant_id)

        self.inventory_repository.adjust_quantity(
            variant_id,
            initial_stock,
        )

        return variant_id

    def _create_sale(
        self,
        sale_number=None,
        subtotal=1000,
        discount=0,
        tax=0,
    ):
        if sale_number is None:
            sale_number = f"TEST-SALE-{uuid4().hex[:12]}"

        return Sale(
            sale_number=sale_number,
            subtotal=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total_amount=subtotal - discount + tax,
        )

    def _stock(self, variant_id):
        inventory = self.inventory_repository.get_by_variant(
            variant_id
        )

        return inventory["quantity_on_hand"]

    def _sale_history_count(self, sale_id):
        return self.sale_item_repository.count_by_sale(sale_id)

    # ==========================================
    # TEST 1: SUCCESSFUL CASH CHECKOUT
    # ==========================================

    def test_successful_cash_checkout(self):
        sale = self._create_sale(
            subtotal=2000,
            discount=0,
            tax=0,
        )

        initial_stock = self._stock(self.variant_1)

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_1,
                    "quantity": 2,
                }
            ],
            payment={
                "payment_method": "CASH",
                "amount": 2000,
            },
        )

        assert result["sale_id"] > 0
        assert result["payment_id"] is not None
        assert len(result["sale_item_ids"]) == 1

        saved_sale = self.sale_repository.get_by_id(
            result["sale_id"]
        )

        assert saved_sale is not None
        assert saved_sale.total_amount == 2000

        assert self._stock(self.variant_1) == initial_stock - 2

        print("Successful cash checkout: PASSED")

    # ==========================================
    # TEST 2: CHECKOUT WITHOUT PAYMENT
    # ==========================================

    def test_checkout_without_payment(self):
        sale = self._create_sale(
            subtotal=1000,
        )

        initial_stock = self._stock(self.variant_1)

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_1,
                    "quantity": 1,
                }
            ],
        )

        assert result["sale_id"] > 0
        assert result["payment_id"] is None

        assert self._stock(self.variant_1) == initial_stock - 1

        print("Checkout without payment: PASSED")

    # ==========================================
    # TEST 3: MULTIPLE VARIANTS
    # ==========================================

    def test_multiple_variants_checkout(self):
        sale = self._create_sale(
            subtotal=4000,
        )

        stock_1 = self._stock(self.variant_1)
        stock_2 = self._stock(self.variant_2)

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_1,
                    "quantity": 2,
                },
                {
                    "variant_id": self.variant_2,
                    "quantity": 1,
                },
            ],
        )

        assert len(result["sale_item_ids"]) == 2

        assert self._stock(self.variant_1) == stock_1 - 2
        assert self._stock(self.variant_2) == stock_2 - 1

        print("Multiple variants checkout: PASSED")

    # ==========================================
    # TEST 4: ITEM DISCOUNT AND TAX
    # ==========================================

    def test_discount_and_tax_calculation(self):
        sale = self._create_sale(
            subtotal=2000,
            discount=200,
            tax=100,
        )

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_2,
                    "quantity": 1,
                    "discount_amount": 200,
                }
            ],
        )

        saved_sale = self.sale_repository.get_by_id(
            result["sale_id"]
        )

        assert saved_sale.subtotal == 2000
        assert saved_sale.discount_amount == 200
        assert saved_sale.tax_amount == 100
        assert saved_sale.total_amount == 1900

        print("Discount and tax calculation: PASSED")

    # ==========================================
    # TEST 5: INVENTORY HISTORY
    # ==========================================

    def test_inventory_history_creation(self):
        sale = self._create_sale(
            subtotal=1000,
        )

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_1,
                    "quantity": 1,
                }
            ],
        )

        history = self.transaction_repository.get_by_variant(
            self.variant_1
        )

        matching_records = [
            transaction
            for transaction in history
            if (
                transaction.reference_type == "SALE"
                and transaction.reference_id == result["sale_id"]
            )
        ]

        assert len(matching_records) == 1

        transaction = matching_records[0]

        assert transaction.transaction_type == "SALE"
        assert transaction.quantity_change == -1

        print("Inventory history creation: PASSED")

    # ==========================================
    # TEST 6: INSUFFICIENT STOCK
    # ==========================================

    def test_insufficient_stock_prevention(self):
        sale = self._create_sale(
            subtotal=10000,
        )

        stock_before = self._stock(self.variant_1)

        sale_number = sale.sale_number

        try:
            self.sale_service.create_sale(
                sale=sale,
                items=[
                    {
                        "variant_id": self.variant_1,
                        "quantity": stock_before + 1,
                    }
                ],
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Insufficient stock was incorrectly accepted."
            )

        assert self._stock(self.variant_1) == stock_before

        assert (
            self.sale_repository.get_by_sale_number(sale_number)
            is None
        )

        print("Insufficient stock prevention: PASSED")

    # ==========================================
    # TEST 7: INVALID VARIANT
    # ==========================================

    def test_invalid_variant_prevention(self):
        sale = self._create_sale(
            subtotal=1000,
        )

        try:
            self.sale_service.create_sale(
                sale=sale,
                items=[
                    {
                        "variant_id": 999999999,
                        "quantity": 1,
                    }
                ],
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Invalid variant was incorrectly accepted."
            )

        assert (
            self.sale_repository.get_by_sale_number(sale.sale_number)
            is None
        )

        print("Invalid variant prevention: PASSED")

    # ==========================================
    # TEST 8: DUPLICATE SALE NUMBER
    # ==========================================

    def test_duplicate_sale_number_prevention(self):
        sale_number = f"DUPLICATE-{uuid4().hex[:10]}"

        first_sale = self._create_sale(
            sale_number=sale_number,
            subtotal=1000,
        )

        self.sale_service.create_sale(
            sale=first_sale,
            items=[
                {
                    "variant_id": self.variant_1,
                    "quantity": 1,
                }
            ],
        )

        second_sale = self._create_sale(
            sale_number=sale_number,
            subtotal=1000,
        )

        try:
            self.sale_service.create_sale(
                sale=second_sale,
                items=[
                    {
                        "variant_id": self.variant_1,
                        "quantity": 1,
                    }
                ],
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Duplicate sale number was incorrectly accepted."
            )

        print("Duplicate sale number prevention: PASSED")

    # ==========================================
    # TEST 9: PAYMENT OVERPAYMENT
    # ==========================================

    def test_payment_overpayment_prevention(self):
        sale = self._create_sale(
            subtotal=1000,
        )

        stock_before = self._stock(self.variant_1)

        try:
            self.sale_service.create_sale(
                sale=sale,
                items=[
                    {
                        "variant_id": self.variant_1,
                        "quantity": 1,
                    }
                ],
                payment={
                    "payment_method": "CASH",
                    "amount": 1500,
                },
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Overpayment was incorrectly accepted."
            )

        assert self._stock(self.variant_1) == stock_before

        assert (
            self.sale_repository.get_by_sale_number(sale.sale_number)
            is None
        )

        print("Payment overpayment prevention: PASSED")

    # ==========================================
    # TEST 10: FULL TRANSACTION ROLLBACK
    # ==========================================

    def test_checkout_rollback(self):
        sale = self._create_sale(
            subtotal=1000,
        )

        stock_before = self._stock(self.variant_1)

        history_before = len(
            self.transaction_repository.get_by_variant(
                self.variant_1
            )
        )

        try:
            self.sale_service.create_sale(
                sale=sale,
                items=[
                    {
                        "variant_id": self.variant_1,
                        "quantity": 1,
                    }
                ],
                payment={
                    # Invalid method causes Payment validation
                    # to fail after sale and stock operations.
                    "payment_method": "INVALID_METHOD",
                    "amount": 1000,
                },
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Invalid payment method was incorrectly accepted."
            )

        # Sale must not exist.
        assert (
            self.sale_repository.get_by_sale_number(sale.sale_number)
            is None
        )

        # Stock must be restored.
        assert self._stock(self.variant_1) == stock_before

        # Inventory history must also be rolled back.
        history_after = len(
            self.transaction_repository.get_by_variant(
                self.variant_1
            )
        )

        assert history_after == history_before

        print("Checkout transaction rollback: PASSED")

    # ==========================================
    # RUN ALL TESTS
    # ==========================================

    def run_tests(self):
        print("\nStarting SaleService tests...\n")

        self.test_successful_cash_checkout()
        self.test_checkout_without_payment()
        self.test_multiple_variants_checkout()
        self.test_discount_and_tax_calculation()
        self.test_inventory_history_creation()
        self.test_insufficient_stock_prevention()
        self.test_invalid_variant_prevention()
        self.test_duplicate_sale_number_prevention()
        self.test_payment_overpayment_prevention()
        self.test_checkout_rollback()

        print("\nAll SaleService tests passed!")


def run_tests():
    test = SaleServiceTest()
    test.run_tests()


if __name__ == "__main__":
    run_tests()
