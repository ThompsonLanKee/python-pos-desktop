
from src.models import SalesReturn, SalesReturnItem


def run_tests():

    # 1. Sales return model
    sales_return = SalesReturn(
        return_number="RET-0001",
        sale_id=1,
        total_refund_amount=2000,
        reason="Customer changed mind",
    )

    assert sales_return.return_number == "RET-0001"
    assert sales_return.return_status == "COMPLETED"

    print("SalesReturn model: PASSED")

    # 2. Return item model
    item = SalesReturnItem(
        return_id=1,
        sale_item_id=10,
        variant_id=5,
        quantity=2,
        unit_refund_amount=1000,
        line_refund_amount=2000,
        restock=1,
        condition="GOOD",
    )

    assert item.quantity == 2
    assert item.line_refund_amount == 2000

    print("SalesReturnItem model: PASSED")

    # 3. Damaged item must not be restocked
    try:
        SalesReturnItem(
            return_id=1,
            sale_item_id=10,
            variant_id=5,
            quantity=1,
            unit_refund_amount=1000,
            line_refund_amount=1000,
            restock=1,
            condition="DAMAGED",
        )
    except ValueError:
        print("Damaged item restock prevention: PASSED")
    else:
        raise AssertionError("Damaged item was allowed to be restocked.")

    # 4. Invalid quantity
    try:
        SalesReturnItem(
            return_id=1,
            sale_item_id=10,
            variant_id=5,
            quantity=0,
            unit_refund_amount=1000,
            line_refund_amount=0,
        )
    except ValueError:
        print("Invalid return quantity prevention: PASSED")
    else:
        raise AssertionError("Invalid return quantity was accepted.")

    # 5. Invalid refund calculation
    try:
        SalesReturnItem(
            return_id=1,
            sale_item_id=10,
            variant_id=5,
            quantity=2,
            unit_refund_amount=1000,
            line_refund_amount=1500,
        )
    except ValueError:
        print("Invalid refund calculation prevention: PASSED")
    else:
        raise AssertionError("Incorrect refund calculation was accepted.")

    print("\nAll Sales Return model tests passed!")


if __name__ == "__main__":
    run_tests()
