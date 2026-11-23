
from src.core.database import Database


def verify_database():

    database = Database()
    database.initialize()
    connection = database.connect()

    try:
        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """

        tables = connection.execute(query).fetchall()

        print("\nPOS DATABASE VERIFICATION")
        print("-" * 35)

        for table in tables:
            print(f"[OK] {table['name']}")

        print("-" * 35)
        print(f"Total tables: {len(tables)}")

        all_expected_tables = {
            "users",
            "roles",
            "permissions",
            "user_roles",
            "role_permissions",
            "categories",
            "products",
            "colors",
            "sizes",
            "product_variants",
            "inventory",
            "inventory_transactions",
            "customers",
            "sales",
            "sale_items",
            "payments",
            "refunds",
            "sales_returns",
            "sales_return_items",
        }

        actual_tables = {table["name"] for table in tables}

        if actual_tables == all_expected_tables:
            print("Database verification successful!")
        else:
            print("Database verification incomplete.")
            print("Missing:", all_expected_tables - actual_tables)

        expected_tables = [
            "customers",
            "sales",
            "sale_items",
            "payments",
            "refunds",
            "sales_returns",
            "sales_return_items",
        ]

        for table_name in expected_tables:
            result = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                """,
                (table_name,)
            ).fetchone()

            assert result is not None, (
                f"Missing table: {table_name}"
            )

            print(f"{table_name}: VERIFIED")

        print("Sales, refund, and return database schema verification passed!")

    finally:
        connection.close()


if __name__ == "__main__":
    verify_database()
