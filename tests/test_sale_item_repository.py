
from contextlib import closing
from uuid import uuid4

from src.core.database import Database
from src.models import Sale, SaleItem
from src.repositories import SaleRepository, SaleItemRepository


def run_tests():

    database = Database()
    database.initialize()

    sale_repo = SaleRepository(database)
    item_repo = SaleItemRepository(database)

    suffix = uuid4().hex[:8]

    # Create a sale header.
    sale_id = sale_repo.create(
        Sale(
            sale_number=f"ITEM-TEST-{suffix}",
            subtotal=30000,
            discount_amount=0,
            tax_amount=0,
            total_amount=30000
        )
    )

    # Find an existing active product variant.
    with closing(database.connect()) as connection:
        row = connection.execute(
            """
            SELECT
                pv.variant_id,
                pv.sku,
                pv.cost_price,
                pv.selling_price,
                p.product_name
            FROM product_variants pv
            INNER JOIN products p
                ON pv.product_id = p.product_id
            WHERE pv.is_active = 1
            LIMIT 1
            """
        ).fetchone()

    assert row is not None, (
        "Create a product variant before running this test."
    )

    # CREATE
    item = SaleItem(
        sale_id=sale_id,
        variant_id=row["variant_id"],
        product_name=row["product_name"],
        sku=row["sku"],
        quantity=2,
        unit_cost=round(row["cost_price"]),
        unit_price=15000,
        discount_amount=0,
        line_total=30000
    )

    item_id = item_repo.create(item)

    assert item_id > 0
    print("Sale item creation: PASSED")

    # GET BY ID
    saved_item = item_repo.get_by_id(item_id)

    assert saved_item is not None
    assert saved_item.quantity == 2
    print("Sale item retrieval: PASSED")

    # GET BY SALE
    items = item_repo.get_by_sale(sale_id)

    assert len(items) == 1
    print("Sale item filtering: PASSED")

    # GET ALL
    all_items = item_repo.get_all()

    assert any(
        item["sale_item_id"] == item_id
        for item in all_items
    )
    print("All sale items retrieval: PASSED")

    # EXISTS
    assert item_repo.exists(item_id)
    print("Sale item existence: PASSED")

    # COUNT
    assert item_repo.count_by_sale(sale_id) == 1
    print("Sale item count: PASSED")

    print("\nAll SaleItemRepository tests passed!")


if __name__ == "__main__":
    run_tests()
