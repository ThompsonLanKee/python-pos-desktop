
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product, ProductVariant, Sale
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
    InventoryTransactionRepository,
    SalesReturnRepository,
)
from src.services.sale_service import SaleService
from src.services.sales_return_service import SalesReturnService


class SalesReturnServiceTest:

    def __init__(self):
        self.database = Database()
        self.database.initialize()

        self.category_repository = CategoryRepository(self.database)
        self.product_repository = ProductRepository(self.database)
        self.variant_repository = ProductVariantRepository(self.database)
        self.inventory_repository = InventoryRepository(self.database)
        self.transaction_repository = InventoryTransactionRepository(
            self.database
        )
        self.return_repository = SalesReturnRepository(self.database)

        self.sale_service = SaleService(self.database)
        self.return_service = SalesReturnService(self.database)

        self.suffix = uuid4().hex[:10]
        self.variant_id = self._create_product()

    # --------------------------------------------------
    # TEST DATA
    # --------------------------------------------------

    def _create_product(self):
        category_id = self.category_repository.create(
            Category(
                category_name=f"Return Category {self.suffix}"
            )
        )

        product_id = self.product_repository.create(
            Product(
                product_name=f"Return Product {self.suffix}",
                category_id=category_id,
                description="Product for sales return tests",
            )
        )

        variant_id = self.variant_repository.create(
            ProductVariant(
                product_id=product_id,
                color_id=None,
                size_id=None,
                sku=f"RETURN-{self.suffix}",
                barcode=None,
                cost_price=500,
                selling_price=1000,
            )
        )

        self.inventory_repository.create(variant_id)
        self.inventory_repository.adjust_quantity(variant_id, 30)

        return variant_id

    def _create_sale(self, quantity=3):
        sale_number = f"RETURN-SALE-{uuid4().hex[:10]}"
        subtotal = quantity * 1000

        sale = Sale(
            sale_number=sale_number,
            subtotal=subtotal,
            discount_amount=0,
            tax_amount=0,
            total_amount=subtotal,
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
                "amount": subtotal,
            },
        )

        return {
            "sale_id": result["sale_id"],
            "sale_item_id": result["sale_item_ids"][0],
            "sale_number": sale_number,
            "quantity": quantity,
        }

    def _stock(self):
        inventory = self.inventory_repository.get_by_variant(
            self.variant_id
        )
        return inventory["quantity_on_hand"]

    def _movement_count(self):
        return len(
            self.transaction_repository.get_by_variant(
                self.variant_id
            )
        )

    def _create_return(
        self,
        sale_data,
        quantity=1,
        restock=True,
        condition="GOOD",
    ):
        return self.return_service.create_return(
            return_number=f"RETURN-{uuid4().hex[:10]}",
            sale_id=sale_data["sale_id"],
            items=[
                {
                    "sale_item_id": sale_data["sale_item_id"],
                    "quantity": quantity,
                    "restock": restock,
                    "condition": condition,
                }
            ],
            reason="Test return",
        )

    # --------------------------------------------------
    # TEST 1: SUCCESSFUL GOOD RETURN
    # --------------------------------------------------

    def test_good_return(self):
        sale_data = self._create_sale(quantity=3)

        stock_before = self._stock()
        movements_before = self._movement_count()

        result = self._create_return(
            sale_data,
            quantity=1,
            restock=True,
            condition="GOOD",
        )

        assert result["return_id"] > 0
        assert result["sale_id"] == sale_data["sale_id"]
        assert result["total_refund_amount"] == 1000
        assert result["item_count"] == 1

        assert self._stock() == stock_before + 1
        assert self._movement_count() == movements_before + 1

        print("Successful good return: PASSED")

    # --------------------------------------------------
    # TEST 2: DAMAGED ITEM IS NOT RESTOCKED
    # --------------------------------------------------

    def test_damaged_return(self):
        sale_data = self._create_sale(quantity=3)

        stock_before = self._stock()
        movements_before = self._movement_count()

        result = self._create_return(
            sale_data,
            quantity=1,
            restock=False,
            condition="DAMAGED",
        )

        assert result["total_refund_amount"] == 1000
        assert self._stock() == stock_before
        assert self._movement_count() == movements_before

        print("Damaged item restock prevention: PASSED")

    # --------------------------------------------------
    # TEST 3: PARTIAL RETURNS
    # --------------------------------------------------

    def test_partial_returns(self):
        sale_data = self._create_sale(quantity=3)

        first = self._create_return(
            sale_data,
            quantity=1,
            restock=True,
            condition="GOOD",
        )

        second = self._create_return(
            sale_data,
            quantity=2,
            restock=False,
            condition="DAMAGED",
        )

        assert first["total_refund_amount"] == 1000
        assert second["total_refund_amount"] == 2000

        remaining = self.return_service.get_returnable_quantity(
            sale_data["sale_item_id"]
        )

        assert remaining == 0

        print("Partial return calculation: PASSED")

    # --------------------------------------------------
    # TEST 4: RETURNABLE QUANTITY
    # --------------------------------------------------

    def test_returnable_quantity(self):
        sale_data = self._create_sale(quantity=3)

        assert (
            self.return_service.get_returnable_quantity(
                sale_data["sale_item_id"]
            ) == 3
        )

        self._create_return(
            sale_data,
            quantity=1,
            restock=False,
            condition="DAMAGED",
        )

        assert (
            self.return_service.get_returnable_quantity(
                sale_data["sale_item_id"]
            ) == 2
        )

        print("Remaining returnable quantity: PASSED")

    # --------------------------------------------------
    # TEST 5: OVER-RETURN PREVENTION
    # --------------------------------------------------

    def test_over_return_prevention(self):
        sale_data = self._create_sale(quantity=2)

        self._create_return(
            sale_data,
            quantity=2,
            restock=False,
            condition="DAMAGED",
        )

        try:
            self._create_return(
                sale_data,
                quantity=1,
                restock=False,
                condition="DAMAGED",
            )
        except ValueError:
            print("Invalid return quantity prevention: PASSED")
        else:
            raise AssertionError(
                "Returning more than the sold quantity was accepted."
            )

    # --------------------------------------------------
    # TEST 6: INVALID SALE ITEM
    # --------------------------------------------------

    def test_invalid_sale_item(self):
        sale_data = self._create_sale(quantity=2)

        try:
            self.return_service.create_return(
                return_number=f"INVALID-{uuid4().hex[:10]}",
                sale_id=sale_data["sale_id"],
                items=[
                    {
                        "sale_item_id": 999999999,
                        "quantity": 1,
                    }
                ],
            )
        except ValueError:
            print("Invalid sale item prevention: PASSED")
        else:
            raise AssertionError(
                "A sale item from another or nonexistent sale was accepted."
            )

    # --------------------------------------------------
    # TEST 7: DUPLICATE SALE ITEM IN ONE RETURN
    # --------------------------------------------------

    def test_duplicate_sale_item(self):
        sale_data = self._create_sale(quantity=3)

        try:
            self.return_service.create_return(
                return_number=f"DUPLICATE-{uuid4().hex[:10]}",
                sale_id=sale_data["sale_id"],
                items=[
                    {
                        "sale_item_id": sale_data["sale_item_id"],
                        "quantity": 1,
                    },
                    {
                        "sale_item_id": sale_data["sale_item_id"],
                        "quantity": 1,
                    },
                ],
            )
        except ValueError:
            print("Duplicate return item prevention: PASSED")
        else:
            raise AssertionError(
                "Duplicate sale items were accepted in one return."
            )

    # --------------------------------------------------
    # TEST 8: DAMAGED ITEM CANNOT BE RESTOCKED
    # --------------------------------------------------

    def test_damaged_item_restock_rejection(self):
        sale_data = self._create_sale(quantity=2)

        stock_before = self._stock()

        try:
            self._create_return(
                sale_data,
                quantity=1,
                restock=True,
                condition="DAMAGED",
            )
        except ValueError:
            assert self._stock() == stock_before
            print("Damaged item restock rejection: PASSED")
        else:
            raise AssertionError(
                "Damaged goods were incorrectly accepted for restocking."
            )

    # --------------------------------------------------
    # TEST 9: RETURN DETAILS
    # --------------------------------------------------

    def test_return_details(self):
        sale_data = self._create_sale(quantity=2)

        result = self._create_return(
            sale_data,
            quantity=1,
        )

        details = self.return_service.get_return_details(
            result["return_id"]
        )

        assert details["return"]["return_id"] == result["return_id"]
        assert details["return"]["sale_id"] == sale_data["sale_id"]
        assert len(details["items"]) == 1

        print("Return details retrieval: PASSED")

    # --------------------------------------------------
    # TEST 10: INVENTORY MOVEMENT HISTORY
    # --------------------------------------------------

    def test_inventory_movement_history(self):
        sale_data = self._create_sale(quantity=2)

        result = self._create_return(
            sale_data,
            quantity=1,
            restock=True,
            condition="GOOD",
        )

        movements = self.transaction_repository.get_by_variant(
            self.variant_id
        )

        matching = [
            movement
            for movement in movements
            if (
                movement.reference_type == "SALES_RETURN"
                and movement.reference_id == result["return_id"]
            )
        ]

        assert len(matching) == 1
        assert matching[0].transaction_type == "SALE_RETURN"
        assert matching[0].quantity_change == 1

        print("Return inventory movement history: PASSED")

    # --------------------------------------------------
    # RUN ALL TESTS
    # --------------------------------------------------

    def run_tests(self):
        print("\nStarting SalesReturnService tests...\n")

        self.test_good_return()
        self.test_damaged_return()
        self.test_partial_returns()
        self.test_returnable_quantity()
        self.test_over_return_prevention()
        self.test_invalid_sale_item()
        self.test_duplicate_sale_item()
        self.test_damaged_item_restock_rejection()
        self.test_return_details()
        self.test_inventory_movement_history()

        print("\nAll SalesReturnService tests passed!")


def run_tests():
    test = SalesReturnServiceTest()
    test.run_tests()


if __name__ == "__main__":
    run_tests()
