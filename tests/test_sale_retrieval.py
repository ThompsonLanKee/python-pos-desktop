
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product, ProductVariant, Sale
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
)
from src.services.sale_service import SaleService


class SaleRetrievalTest:

    def __init__(self):
        self.database = Database()
        self.database.initialize()

        self.category_repository = CategoryRepository(self.database)
        self.product_repository = ProductRepository(self.database)
        self.variant_repository = ProductVariantRepository(self.database)
        self.inventory_repository = InventoryRepository(self.database)

        self.sale_service = SaleService(self.database)

        self.suffix = uuid4().hex[:10]

        self.variant_id = None
        self.sale_id = None
        self.sale_number = None

        self._create_test_sale()

    # ==========================================
    # TEST DATA
    # ==========================================

    def _create_test_sale(self):

        category_id = self.category_repository.create(
            Category(
                category_name=f"Retrieval Category {self.suffix}"
            )
        )

        product_id = self.product_repository.create(
            Product(
                product_name=f"Retrieval Product {self.suffix}",
                category_id=category_id,
                description="Product for sale retrieval tests",
            )
        )

        self.variant_id = self.variant_repository.create(
            ProductVariant(
                product_id=product_id,
                color_id=None,
                size_id=None,
                sku=f"RETRIEVAL-{self.suffix}",
                barcode=None,
                cost_price=500,
                selling_price=1000,
            )
        )

        self.inventory_repository.create(self.variant_id)

        self.inventory_repository.adjust_quantity(
            self.variant_id,
            10
        )

        self.sale_number = f"RETRIEVAL-SALE-{self.suffix}"

        sale = Sale(
            sale_number=self.sale_number,
            subtotal=2000,
            discount_amount=0,
            tax_amount=0,
            total_amount=2000,
        )

        result = self.sale_service.create_sale(
            sale=sale,
            items=[
                {
                    "variant_id": self.variant_id,
                    "quantity": 2,
                }
            ],
        )

        self.sale_id = result["sale_id"]

        assert self.sale_id > 0

    # ==========================================
    # TEST 1: SALE DETAILS
    # ==========================================

    def test_sale_details(self):

        details = self.sale_service.get_sale_details(
            self.sale_id
        )

        assert details["sale"]["sale_id"] == self.sale_id
        assert details["sale"]["sale_number"] == self.sale_number

        assert isinstance(details["items"], list)
        assert len(details["items"]) == 1

        assert isinstance(details["payments"], list)

        print("Sale details retrieval: PASSED")

    # ==========================================
    # TEST 2: RETRIEVE BY SALE NUMBER
    # ==========================================

    def test_sale_by_number(self):

        details = self.sale_service.get_sale_by_number(
            self.sale_number
        )

        assert details["sale"]["sale_id"] == self.sale_id
        assert details["sale"]["sale_number"] == self.sale_number

        print("Sale number retrieval: PASSED")

    # ==========================================
    # TEST 3: SALE ITEM DETAILS
    # ==========================================

    def test_sale_items(self):

        details = self.sale_service.get_sale_details(
            self.sale_id
        )

        items = details["items"]

        assert len(items) == 1

        item = items[0]

        assert item["variant_id"] == self.variant_id
        assert item["quantity"] == 2
        assert item["sku"]
        assert item["line_total"] == 2000

        print("Sale item details retrieval: PASSED")

    # ==========================================
    # TEST 4: PAYMENT SUMMARY
    # ==========================================

    def test_payment_summary(self):

        details = self.sale_service.get_sale_details(
            self.sale_id
        )

        summary = details["payment_summary"]

        assert summary["total_amount"] == 2000
        assert summary["paid_amount"] == 0
        assert summary["outstanding_balance"] == 2000

        print("Payment summary retrieval: PASSED")

    # ==========================================
    # TEST 5: RECEIPT DATA
    # ==========================================

    def test_receipt_data(self):

        receipt = self.sale_service.get_receipt_data(
            self.sale_id
        )

        assert receipt["receipt_number"] == self.sale_number
        assert receipt["total_amount"] == 2000
        assert isinstance(receipt["items"], list)
        assert len(receipt["items"]) == 1

        print("Receipt data generation: PASSED")

    # ==========================================
    # TEST 6: INVALID SALE ID
    # ==========================================

    def test_invalid_sale_id(self):

        try:
            self.sale_service.get_sale_details(999999999)

        except ValueError:
            print("Invalid sale prevention: PASSED")

        else:
            raise AssertionError(
                "Invalid sale ID was accepted."
            )

    # ==========================================
    # RUN ALL TESTS
    # ==========================================

    def run_tests(self):

        print("\nStarting Sale Retrieval tests...\n")

        self.test_sale_details()
        self.test_sale_by_number()
        self.test_sale_items()
        self.test_payment_summary()
        self.test_receipt_data()
        self.test_invalid_sale_id()

        print("\nAll Sale Retrieval tests passed!")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    test = SaleRetrievalTest()
    test.run_tests()
