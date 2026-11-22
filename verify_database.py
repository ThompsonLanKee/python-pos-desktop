
from src.core.database import Database


def verify_database():

    database = Database()
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

        expected_tables = {
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
            "inventory_transactions"
        }

        actual_tables = {table["name"] for table in tables}

        if actual_tables == expected_tables:
            print("Database verification successful!")
        else:
            print("Database verification incomplete.")
            print("Missing:", expected_tables - actual_tables)

    finally:
        connection.close()


if __name__ == "__main__":
    verify_database()
