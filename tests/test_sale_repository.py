
from uuid import uuid4

from src.core.database import Database
from src.models import Sale
from src.repositories import SaleRepository


def run_tests():

    database = Database()
    database.initialize()

    repository = SaleRepository(database)

    suffix = uuid4().hex[:8]
    sale_number = f"SALE-{suffix}"

    # CREATE
    sale_id = repository.create(
        Sale(
            sale_number=sale_number,
            subtotal=50000,
            discount_amount=5000,
            tax_amount=0,
            total_amount=45000,
            notes="Repository test"
        )
    )

    assert sale_id > 0
    print("Sale creation: PASSED")

    # GET BY ID
    sale = repository.get_by_id(sale_id)

    assert sale is not None
    assert sale.sale_number == sale_number
    print("Sale retrieval by ID: PASSED")

    # GET BY SALE NUMBER
    sale = repository.get_by_sale_number(sale_number)

    assert sale is not None
    assert sale.sale_id == sale_id
    print("Sale receipt lookup: PASSED")

    # GET ALL
    sales = repository.get_all()

    assert any(item.sale_id == sale_id for item in sales)
    print("All sales retrieval: PASSED")

    # GET BY STATUS
    completed_sales = repository.get_by_status("COMPLETED")

    assert any(item.sale_id == sale_id for item in completed_sales)
    print("Sales status filtering: PASSED")

    # UPDATE STATUS
    assert repository.update_status(sale_id, "VOIDED")

    updated = repository.get_by_id(sale_id)

    assert updated.sale_status == "VOIDED"
    print("Sale status update: PASSED")

    # FILTER BY DATE
    date_sales = repository.get_by_date_range(
        updated.created_at[:10],
        updated.created_at[:10]
    )

    assert any(item.sale_id == sale_id for item in date_sales)
    print("Sale date filtering: PASSED")

    # EXISTS
    assert repository.exists(sale_id)
    assert repository.exists_by_sale_number(sale_number)
    print("Sale existence checks: PASSED")

    # INVALID STATUS
    try:
        repository.update_status(sale_id, "INVALID")

    except ValueError:
        print("Invalid sale status prevention: PASSED")

    else:
        raise AssertionError("Invalid status was accepted.")

    print("\nAll SaleRepository tests passed!")


if __name__ == "__main__":
    run_tests()
