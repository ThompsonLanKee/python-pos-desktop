
from uuid import uuid4
from contextlib import closing

from src.core.database import Database


database = Database()

category_name = f"Rollback Test {uuid4().hex}"

try:
    with database.transaction() as connection:

        # First operation succeeds.
        connection.execute(
            """
            INSERT INTO categories (
                category_name,
                is_active
            )
            VALUES (?, 1)
            """,
            (category_name,)
        )

        # Simulate a failure after the successful insert.
        raise RuntimeError("Simulated transaction failure.")

except RuntimeError:
    print("Transaction failure detected.")

# Verify that the earlier insert was rolled back.
with closing(database.connect()) as connection:

    row = connection.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = ?
        """,
        (category_name,)
    ).fetchone()

    assert row is None, (
        "Rollback failed: category still exists."
    )

print("Transaction rollback verification: PASSED")
