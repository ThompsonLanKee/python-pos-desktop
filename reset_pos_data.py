"""
FULL MOCK-DATA RESET FOR THE POS PROJECT

Run from the project root:
    python reset_pos_data.py

This version physically deletes mock catalog and transaction data:
- categories, products, product_variants, inventory
- colors, sizes, inventory_transactions
- sales, sale_items, payments, refunds
- sales_returns, sales_return_items

It keeps:
- customers
- permission definitions
- exactly one user: lankee (existing password_hash retained)

It rebuilds roles as one Administrator role and grants it every permission.
A database backup is created before any changes.
The reset is transactional and checks for unexpected foreign-key dependants.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

from src.core.database import DATABASE_PATH

KEEP_USERNAME = "lankee"

# Child tables must be deleted before their parent tables.
DELETE_ORDER = [
    "refunds",
    "sales_return_items",
    "sales_returns",
    "sale_items",
    "payments",
    "inventory_transactions",
    "inventory",
    "product_variants",
    "products",
    "categories",
    "colors",
    "sizes",
    "sales",
]

ROLE_TABLES = ["user_roles", "role_permissions", "roles"]


def backup_database(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(
        f"{db_path.stem}_backup_{stamp}{db_path.suffix}"
    )
    with sqlite3.connect(str(db_path)) as source:
        with sqlite3.connect(str(backup_path)) as destination:
            source.backup(destination)
    return backup_path


def table_exists(conn, table_name):
    return conn.execute("""
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (table_name,)).fetchone() is not None


def get_user_reference_blockers(conn, ignored_tables):
    """Find retained rows that would prevent deleting users or roles."""
    blockers = []
    rows = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for (child_table,) in rows:
        if child_table in ignored_tables:
            continue

        for fk in conn.execute(
            f'PRAGMA foreign_key_list("{child_table}")'
        ).fetchall():
            parent_table = fk[2]
            if parent_table not in {"users", "roles"}:
                continue

            child_column = fk[3]
            parent_column = fk[4] or "rowid"
            sql = (
                f'SELECT COUNT(*) FROM "{child_table}" child '
                f'JOIN "{parent_table}" parent '
                f'ON child."{child_column}" = parent."{parent_column}"'
            )
            count = conn.execute(sql).fetchone()[0]
            if count:
                blockers.append(
                    f"{child_table}.{child_column} -> "
                    f"{parent_table}: {count} row(s)"
                )
    return blockers


def get_catalog_reference_blockers(conn, deleted_tables):
    """Find references from tables not included in the reset."""
    blockers = []
    rows = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for (child_table,) in rows:
        if child_table in deleted_tables:
            continue

        for fk in conn.execute(
            f'PRAGMA foreign_key_list("{child_table}")'
        ).fetchall():
            parent_table = fk[2]
            if parent_table not in deleted_tables:
                continue

            child_column = fk[3]
            parent_column = fk[4] or "rowid"
            sql = (
                f'SELECT COUNT(*) FROM "{child_table}" child '
                f'JOIN "{parent_table}" parent '
                f'ON child."{child_column}" = parent."{parent_column}"'
            )
            count = conn.execute(sql).fetchone()[0]
            if count:
                blockers.append(
                    f"{child_table}.{child_column} -> "
                    f"{parent_table}: {count} row(s)"
                )
    return blockers


def seed_clean_reference_data(conn):
    # Categories: parent categories first.
    category_rows = [
        ("Clothing", "Clothing and apparel", None),
        ("Electronics", "Electronic products and accessories", None),
        ("Grocery", "Food, beverages and grocery items", None),
        ("General", "General merchandise", None),
    ]
    category_ids = {}

    for name, description, parent_id in category_rows:
        cursor = conn.execute("""
            INSERT INTO categories (
                category_name, description, parent_category_id, is_active
            )
            VALUES (?, ?, ?, 1)
        """, (name, description, parent_id))
        category_ids[name] = cursor.lastrowid

    subcategories = [
        ("Men", "Men's clothing", "Clothing"),
        ("Women", "Women's clothing", "Clothing"),
        ("Kids", "Children's clothing", "Clothing"),
        ("Mobile Accessories", "Accessories for mobile devices", "Electronics"),
        ("Computer Accessories", "Accessories for computers", "Electronics"),
        ("Beverages", "Drinks and beverages", "Grocery"),
        ("Snacks", "Packaged snacks and snack foods", "Grocery"),
    ]

    for name, description, parent_name in subcategories:
        cursor = conn.execute("""
            INSERT INTO categories (
                category_name, description, parent_category_id, is_active
            )
            VALUES (?, ?, ?, 1)
        """, (name, description, category_ids[parent_name]))
        category_ids[name] = cursor.lastrowid

    conn.executemany("""
        INSERT INTO colors (color_name, hex_code, is_active)
        VALUES (?, ?, 1)
    """, [
        ("Black", "#000000"),
        ("White", "#FFFFFF"),
        ("Red", "#FF0000"),
        ("Blue", "#0000FF"),
        ("Green", "#008000"),
        ("Gray", "#808080"),
    ])

    conn.executemany("""
        INSERT INTO sizes (size_name, sort_order, is_active)
        VALUES (?, ?, 1)
    """, [
        ("XS", 1),
        ("S", 2),
        ("M", 3),
        ("L", 4),
        ("XL", 5),
        ("XXL", 6),
    ])


def reset_database():
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    backup_path = backup_database(db_path)
    print(f"Backup created: {backup_path}")

    conn = sqlite3.connect(str(db_path), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 20000")

    try:
        conn.execute("BEGIN IMMEDIATE")

        required = [
            "users", "roles", "permissions", "user_roles",
            "role_permissions", "categories", "products", "colors",
            "sizes", "product_variants", "inventory",
            "inventory_transactions", "sales", "sale_items",
            "payments", "sales_returns", "sales_return_items",
        ]
        missing = [name for name in required if not table_exists(conn, name)]
        if missing:
            raise RuntimeError(
                "Required tables are missing: " + ", ".join(missing)
            )

        keeper = conn.execute("""
            SELECT user_id, password_hash
            FROM users
            WHERE username = ? COLLATE NOCASE
        """, (KEEP_USERNAME,)).fetchone()

        if keeper is None:
            raise RuntimeError(
                "User 'lankee' was not found. No data was changed."
            )

        permission_count = conn.execute(
            "SELECT COUNT(*) FROM permissions"
        ).fetchone()[0]
        if permission_count == 0:
            raise RuntimeError(
                "Permission definitions are empty. Cannot grant all access."
            )

        delete_tables = set(DELETE_ORDER)

        # Abort if an unplanned table still references catalog/transaction data.
        catalog_blockers = get_catalog_reference_blockers(
            conn, delete_tables
        )
        if catalog_blockers:
            raise RuntimeError(
                "Unexpected tables reference data scheduled for deletion:\n - "
                + "\n - ".join(catalog_blockers)
                + "\nAdd those mock dependent tables to DELETE_ORDER only "
                  "after confirming they contain test data."
            )

        # sales_returns is deleted before users; user_roles/role_permissions
        # and roles are rebuilt. Detect any other retained user/role references.
        ignored_user_role_children = {
            "user_roles", "role_permissions"
        } | delete_tables

        user_role_blockers = get_user_reference_blockers(
            conn, ignored_user_role_children
        )
        if user_role_blockers:
            raise RuntimeError(
                "Other tables reference users or roles:\n - "
                + "\n - ".join(user_role_blockers)
                + "\nNo data was changed."
            )

        # Delete mock sales and catalog data in dependency order.
        for table in DELETE_ORDER:
            if table_exists(conn, table):
                conn.execute(f'DELETE FROM "{table}"')

        # Delete other users, retaining lankee and the current password hash.
        conn.execute("DELETE FROM user_roles")
        conn.execute("DELETE FROM role_permissions")
        conn.execute("DELETE FROM roles")
        conn.execute("""
            DELETE FROM users
            WHERE username != ? COLLATE NOCASE
        """, (KEEP_USERNAME,))
        conn.execute("""
            UPDATE users
            SET is_active = 1
            WHERE user_id = ?
        """, (keeper["user_id"],))

        # Create one Administrator role with all defined permissions.
        conn.execute("""
            INSERT INTO roles (role_name, description)
            VALUES (?, ?)
        """, (
            "Administrator",
            "Full access to all application permissions."
        ))
        admin_role_id = conn.execute("""
            SELECT role_id FROM roles
            WHERE role_name = 'Administrator'
        """).fetchone()["role_id"]

        conn.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT ?, permission_id FROM permissions
        """, (admin_role_id,))
        conn.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
        """, (keeper["user_id"], admin_role_id))

        # Reset AUTOINCREMENT counters for tables physically emptied.
        if table_exists(conn, "sqlite_sequence"):
            for table in DELETE_ORDER:
                conn.execute(
                    "DELETE FROM sqlite_sequence WHERE name = ?",
                    (table,)
                )

        # Insert clean starter category/color/size data.
        seed_clean_reference_data(conn)

        # Final checks before commit.
        remaining_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        remaining_products = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        remaining_variants = conn.execute(
            "SELECT COUNT(*) FROM product_variants"
        ).fetchone()[0]
        remaining_sales = conn.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        granted = conn.execute("""
            SELECT COUNT(*)
            FROM role_permissions rp
            JOIN user_roles ur ON ur.role_id = rp.role_id
            WHERE ur.user_id = ?
        """, (keeper["user_id"],)).fetchone()[0]

        if (
            remaining_users != 1
            or remaining_products != 0
            or remaining_variants != 0
            or remaining_sales != 0
            or granted != permission_count
        ):
            raise RuntimeError(
                "Final verification failed; transaction will be rolled back."
            )

        conn.commit()

        print("\nFULL MOCK-DATA RESET COMPLETED")
        print("--------------------------------")
        print("Products: deleted")
        print("Variants: deleted")
        print("Categories: old records deleted; clean starter categories inserted")
        print("Colors: old records deleted; clean colors inserted")
        print("Sizes: old records deleted; clean sizes inserted")
        print("Inventory and inventory transactions: deleted")
        print("Sales, sale items, payments, refunds and returns: deleted")
        print("Customers: preserved")
        print("Permission definitions: preserved")
        print("Users remaining: lankee only")
        print("Password hash: preserved")
        print("Role: Administrator")
        print(f"Permissions assigned: {granted}")
        print(f"Backup: {backup_path}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        reset_database()
    except Exception as error:
        print("\nRESET NOT COMPLETED")
        print(error)
        print("All database changes were rolled back.")
        raise
