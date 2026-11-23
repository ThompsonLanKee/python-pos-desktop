
from src.models import Customer, Sale, SaleItem, Payment


def run_tests():

    # Customer
    customer = Customer(
        customer_name="  John Doe  ",
        phone="09123456789"
    )

    assert customer.customer_name == "John Doe"
    print("Customer model: PASSED")

    # Sale
    sale = Sale(
        sale_number="SALE-001",
        subtotal=50000,
        discount_amount=5000,
        tax_amount=0,
        total_amount=45000
    )

    assert sale.total_amount == 45000
    print("Sale model: PASSED")

    # Sale item
    item = SaleItem(
        sale_id=1,
        variant_id=1,
        product_name="Cotton T-Shirt",
        sku="TSHIRT-BLK-M",
        quantity=2,
        unit_cost=10000,
        unit_price=15000,
        discount_amount=0,
        line_total=30000
    )

    assert item.line_total == 30000
    print("Sale item model: PASSED")

    # Payment
    payment = Payment(
        sale_id=1,
        payment_method="cash",
        amount=45000
    )

    assert payment.payment_method == "CASH"
    print("Payment model: PASSED")

    # Invalid sale total
    try:
        Sale(
            sale_number="SALE-002",
            subtotal=50000,
            discount_amount=5000,
            tax_amount=0,
            total_amount=50000
        )

    except ValueError:
        print("Invalid sale total prevention: PASSED")

    else:
        raise AssertionError("Invalid sale total was accepted.")

    # Invalid payment
    try:
        Payment(
            sale_id=1,
            payment_method="CASH",
            amount=-100
        )

    except ValueError:
        print("Invalid payment amount prevention: PASSED")

    else:
        raise AssertionError("Invalid payment amount was accepted.")

    print("\nAll sales model tests passed!")


if __name__ == "__main__":
    run_tests()
