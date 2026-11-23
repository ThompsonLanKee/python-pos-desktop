
from uuid import uuid4

from src.core.database import Database
from src.models import Customer
from src.repositories import CustomerRepository


def run_tests():

    database = Database()
    database.initialize()

    repository = CustomerRepository(database)

    suffix = uuid4().hex[:8]
    phone = f"09{suffix[:8]}"

    # CREATE
    customer_id = repository.create(
        Customer(
            customer_name=f"John Doe {suffix}",
            phone=phone,
            email=f"john_{suffix}@example.com",
            address="Yangon"
        )
    )

    assert customer_id > 0
    print("Customer creation: PASSED")

    # GET BY ID
    customer = repository.get_by_id(customer_id)

    assert customer is not None
    assert customer.phone == phone
    print("Customer retrieval: PASSED")

    # GET ALL
    customers = repository.get_all()

    assert any(
        item.customer_id == customer_id
        for item in customers
    )
    print("All customers retrieval: PASSED")

    # GET ACTIVE
    active_customers = repository.get_active()

    assert any(
        item.customer_id == customer_id
        for item in active_customers
    )
    print("Active customers retrieval: PASSED")

    # SEARCH
    results = repository.search(f"John Doe {suffix}")

    assert any(
        item.customer_id == customer_id
        for item in results
    )
    print("Customer search: PASSED")

    # GET BY PHONE
    customer = repository.get_by_phone(phone)

    assert customer is not None
    assert customer.customer_id == customer_id
    print("Customer phone lookup: PASSED")

    # UPDATE
    customer.customer_name = f"John Updated {suffix}"
    customer.address = "Mandalay"

    assert repository.update(customer)

    updated = repository.get_by_id(customer_id)

    assert updated.customer_name == f"John Updated {suffix}"
    assert updated.address == "Mandalay"
    print("Customer update: PASSED")

    # EXISTS
    assert repository.exists(customer_id)
    print("Customer existence check: PASSED")

    # PHONE DUPLICATE CHECK
    assert repository.exists_by_phone(phone)

    assert not repository.exists_by_phone(
        phone,
        exclude_customer_id=customer_id
    )
    print("Customer phone duplicate check: PASSED")

    # DEACTIVATE
    assert repository.set_active(customer_id, False)

    inactive = repository.get_by_id(customer_id)

    assert inactive.is_active == 0
    print("Customer deactivation: PASSED")

    # ACTIVATE
    assert repository.set_active(customer_id, True)

    active = repository.get_by_id(customer_id)

    assert active.is_active == 1
    print("Customer activation: PASSED")

    print("\nAll CustomerRepository tests passed!")


if __name__ == "__main__":
    run_tests()
