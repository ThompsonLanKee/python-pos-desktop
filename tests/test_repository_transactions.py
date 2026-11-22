from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product
from src.repositories import CategoryRepository, ProductRepository


def test_product_mutations_share_caller_transaction():
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "pos.db"

        with patch("src.core.database.DATABASE_PATH", database_path):
            database = Database()
            database.initialize()

            category_id = CategoryRepository(database).create(
                Category(category_name=f"Transaction test {uuid4().hex}")
            )
            product_repository = ProductRepository(database)
            product_id = None

            try:
                with database.transaction() as connection:
                    product = Product(
                        product_name="Uncommitted product",
                        category_id=category_id
                    )
                    product_id = product_repository.create(
                        product,
                        connection=connection
                    )

                    product.product_id = product_id
                    product.product_name = "Updated uncommitted product"

                    assert product_repository.update(
                        product,
                        connection=connection
                    )
                    assert product_repository.set_active(
                        product_id,
                        False,
                        connection=connection
                    )

                    row = connection.execute(
                        """
                        SELECT product_name, is_active
                        FROM products
                        WHERE product_id = ?
                        """,
                        (product_id,)
                    ).fetchone()

                    assert row["product_name"] == "Updated uncommitted product"
                    assert row["is_active"] == 0

                    raise RuntimeError("rollback transaction")
            except RuntimeError as error:
                if str(error) != "rollback transaction":
                    raise

            assert product_id is not None
            assert product_repository.get_by_id(product_id) is None


if __name__ == "__main__":
    test_product_mutations_share_caller_transaction()
    print("Product repository transaction test passed.")
