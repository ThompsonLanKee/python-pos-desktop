
import sqlite3

from contextlib import closing, contextmanager
from pathlib import Path


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "pos.db"

DATABASE_TIMEOUT = 10


class Database:
    """
    Centralized SQLite database manager.

    Responsibilities:
        - Database connection management
        - Foreign key enforcement
        - WAL journal mode
        - Connection timeout
        - Database schema initialization
        - Database debugging
    """

    def __init__(self):

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    # ==================================================
    # CONNECTION MANAGEMENT
    # ==================================================

    def connect(self) -> sqlite3.Connection:
        """
        Create and configure a SQLite connection.
        """

        connection = sqlite3.connect(
            str(DATABASE_PATH),
            timeout=DATABASE_TIMEOUT
        )

        # Dictionary-like row access
        connection.row_factory = sqlite3.Row

        # Enable foreign key constraints
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        # Wait when the database is temporarily locked
        connection.execute(
            "PRAGMA busy_timeout = 10000"
        )

        # Balanced performance and durability in WAL mode
        connection.execute(
            "PRAGMA synchronous = NORMAL"
        )

        return connection

    # ==================================================
    # DATABASE INITIALIZATION
    # ==================================================

    def initialize(self):
        """
        Initialize database tables and indexes.
        """

        with closing(self.connect()) as connection:

            # Enable WAL mode
            connection.execute(
                "PRAGMA journal_mode = WAL"
            )

            with connection:

                connection.executescript("""

                    -- ==================================
                    -- USERS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS users (

                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        username TEXT NOT NULL UNIQUE,

                        password_hash TEXT NOT NULL,

                        full_name TEXT NOT NULL,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),

                        created_at TEXT NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                    );


                    -- ==================================
                    -- ROLES
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS roles (

                        role_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        role_name TEXT NOT NULL UNIQUE,

                        description TEXT
                    );


                    -- ==================================
                    -- PERMISSIONS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS permissions (

                        permission_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        permission_code TEXT NOT NULL UNIQUE,

                        description TEXT
                    );


                    -- ==================================
                    -- USER ROLES
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS user_roles (

                        user_id INTEGER NOT NULL,

                        role_id INTEGER NOT NULL,

                        PRIMARY KEY (user_id, role_id),

                        FOREIGN KEY (user_id)
                            REFERENCES users(user_id)
                            ON DELETE CASCADE,

                        FOREIGN KEY (role_id)
                            REFERENCES roles(role_id)
                            ON DELETE CASCADE
                    );


                    -- ==================================
                    -- ROLE PERMISSIONS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS role_permissions (

                        role_id INTEGER NOT NULL,

                        permission_id INTEGER NOT NULL,

                        PRIMARY KEY (role_id, permission_id),

                        FOREIGN KEY (role_id)
                            REFERENCES roles(role_id)
                            ON DELETE CASCADE,

                        FOREIGN KEY (permission_id)
                            REFERENCES permissions(permission_id)
                            ON DELETE CASCADE
                    );


                    -- ==================================
                    -- INDEXES
                    -- ==================================

                    CREATE INDEX IF NOT EXISTS idx_user_roles_role
                    ON user_roles(role_id);


                    CREATE INDEX IF NOT EXISTS idx_role_permissions_permission
                    ON role_permissions(permission_id);

                    -- ==================================
                    -- CATEGORIES
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS categories (

                        category_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        category_name TEXT NOT NULL COLLATE NOCASE UNIQUE
                            CHECK (length(trim(category_name)) > 0),

                        description TEXT,

                        parent_category_id INTEGER,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (parent_category_id)
                            REFERENCES categories(category_id)
                            ON DELETE SET NULL
                    );


                    -- ==================================
                    -- PRODUCTS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS products (

                        product_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        product_name TEXT NOT NULL
                            CHECK (length(trim(product_name)) > 0),

                        description TEXT,

                        category_id INTEGER NOT NULL,

                        brand TEXT,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (category_id)
                            REFERENCES categories(category_id)
                            ON DELETE RESTRICT
                    );


                    -- ==================================
                    -- COLORS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS colors (

                        color_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        color_name TEXT NOT NULL COLLATE NOCASE UNIQUE
                            CHECK (length(trim(color_name)) > 0),

                        hex_code TEXT,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1))
                    );


                    -- ==================================
                    -- SIZES
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS sizes (

                        size_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        size_name TEXT NOT NULL COLLATE NOCASE UNIQUE
                            CHECK (length(trim(size_name)) > 0),

                        sort_order INTEGER NOT NULL DEFAULT 0,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1))
                    );


                    -- ==================================
                    -- PRODUCT VARIANTS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS product_variants (

                        variant_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        product_id INTEGER NOT NULL,

                        sku TEXT COLLATE NOCASE UNIQUE,

                        barcode TEXT COLLATE NOCASE UNIQUE,

                        color_id INTEGER,

                        size_id INTEGER,

                        cost_price REAL NOT NULL DEFAULT 0
                            CHECK (cost_price >= 0),

                        selling_price REAL NOT NULL DEFAULT 0
                            CHECK (selling_price >= 0),

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (product_id)
                            REFERENCES products(product_id)
                            ON DELETE CASCADE,

                        FOREIGN KEY (color_id)
                            REFERENCES colors(color_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (size_id)
                            REFERENCES sizes(size_id)
                            ON DELETE RESTRICT,

                        UNIQUE (product_id, color_id, size_id)
                    );


                    -- ==================================
                    -- INVENTORY
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS inventory (

                        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        variant_id INTEGER NOT NULL UNIQUE,

                        quantity_on_hand INTEGER NOT NULL DEFAULT 0
                            CHECK (quantity_on_hand >= 0),

                        reorder_level INTEGER NOT NULL DEFAULT 0
                            CHECK (reorder_level >= 0),

                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (variant_id)
                            REFERENCES product_variants(variant_id)
                            ON DELETE CASCADE
                    );

                    -- ==================================
                    -- INVENTORY TRANSACTION HISTORY
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS inventory_transactions (

                        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        variant_id INTEGER NOT NULL,

                        transaction_type TEXT NOT NULL
                            CHECK (
                                transaction_type IN (
                                    'OPENING',
                                    'PURCHASE',
                                    'SALE',
                                    'SALE_RETURN',
                                    'PURCHASE_RETURN',
                                    'ADJUSTMENT_IN',
                                    'ADJUSTMENT_OUT',
                                    'DAMAGE'
                                )
                            ),

                        quantity_change INTEGER NOT NULL
                            CHECK (quantity_change != 0),

                        quantity_after INTEGER NOT NULL
                            CHECK (quantity_after >= 0),

                        reference_type TEXT,

                        reference_id INTEGER,

                        notes TEXT,

                        created_at TEXT NOT NULL
                            DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (variant_id)
                            REFERENCES product_variants(variant_id)
                            ON DELETE RESTRICT
                    );

                    -- ==================================
                    -- CUSTOMERS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS customers (

                        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        customer_name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        address TEXT,

                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );


                    -- ==================================
                    -- SALES
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS sales (

                        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        sale_number TEXT NOT NULL UNIQUE COLLATE NOCASE,

                        customer_id INTEGER,
                        cashier_user_id INTEGER,

                        subtotal INTEGER NOT NULL DEFAULT 0
                            CHECK (subtotal >= 0),

                        discount_amount INTEGER NOT NULL DEFAULT 0
                            CHECK (discount_amount >= 0),

                        tax_amount INTEGER NOT NULL DEFAULT 0
                            CHECK (tax_amount >= 0),

                        total_amount INTEGER NOT NULL DEFAULT 0
                            CHECK (
                                total_amount = subtotal - discount_amount + tax_amount
                            ),

                        sale_status TEXT NOT NULL DEFAULT 'COMPLETED'
                            CHECK (
                                sale_status IN (
                                    'COMPLETED',
                                    'VOIDED',
                                    'REFUNDED'
                                )
                            ),

                        notes TEXT,

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (customer_id)
                            REFERENCES customers(customer_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (cashier_user_id)
                            REFERENCES users(user_id)
                            ON DELETE SET NULL,

                        CHECK (discount_amount <= subtotal)
                    );


                    -- ==================================
                    -- SALE ITEMS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS sale_items (

                        sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        sale_id INTEGER NOT NULL,
                        variant_id INTEGER NOT NULL,

                        product_name TEXT NOT NULL,
                        sku TEXT NOT NULL,

                        quantity INTEGER NOT NULL
                            CHECK (quantity > 0),

                        unit_cost INTEGER NOT NULL
                            CHECK (unit_cost >= 0),

                        unit_price INTEGER NOT NULL
                            CHECK (unit_price >= 0),

                        discount_amount INTEGER NOT NULL DEFAULT 0
                            CHECK (discount_amount >= 0),

                        line_total INTEGER NOT NULL
                            CHECK (
                                line_total = (quantity * unit_price) - discount_amount
                            ),

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (sale_id)
                            REFERENCES sales(sale_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (variant_id)
                            REFERENCES product_variants(variant_id)
                            ON DELETE RESTRICT,

                        CHECK (discount_amount <= quantity * unit_price)
                    );


                    -- ==================================
                    -- PAYMENTS
                    -- ==================================

                    CREATE TABLE IF NOT EXISTS payments (

                        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        sale_id INTEGER NOT NULL,

                        payment_method TEXT NOT NULL
                            CHECK (
                                payment_method IN (
                                    'CASH',
                                    'CARD',
                                    'MOBILE',
                                    'BANK_TRANSFER',
                                    'OTHER'
                                )
                            ),

                        amount INTEGER NOT NULL
                            CHECK (amount > 0),

                        payment_status TEXT NOT NULL DEFAULT 'COMPLETED'
                            CHECK (
                                payment_status IN (
                                    'COMPLETED',
                                    'FAILED',
                                    'REFUNDED'
                                )
                            ),

                        reference_number TEXT,
                        notes TEXT,

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (sale_id)
                            REFERENCES sales(sale_id)
                            ON DELETE RESTRICT
                    );

                    CREATE TABLE IF NOT EXISTS refunds (

                        refund_id INTEGER PRIMARY KEY AUTOINCREMENT,

                        payment_id INTEGER NOT NULL,
                        sale_id INTEGER NOT NULL,
                        return_id INTEGER,

                        amount INTEGER NOT NULL
                            CHECK (amount > 0),

                        reference_number TEXT,
                        notes TEXT,

                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (payment_id)
                            REFERENCES payments(payment_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (sale_id)
                            REFERENCES sales(sale_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (return_id)
                            REFERENCES sales_returns(return_id)
                            ON DELETE RESTRICT
                    );

                    CREATE TABLE IF NOT EXISTS sales_returns (

                        return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        return_number TEXT NOT NULL COLLATE NOCASE UNIQUE,
                        sale_id INTEGER NOT NULL,
                        processed_by INTEGER,
                        return_status TEXT NOT NULL DEFAULT 'COMPLETED'
                            CHECK (
                                return_status IN ('COMPLETED', 'VOIDED')
                            ),
                        total_refund_amount INTEGER NOT NULL DEFAULT 0
                            CHECK (total_refund_amount >= 0),
                        reason TEXT,
                        notes TEXT,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (sale_id)
                            REFERENCES sales(sale_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (processed_by)
                            REFERENCES users(user_id)
                            ON DELETE RESTRICT
                    );

                    CREATE TABLE IF NOT EXISTS sales_return_items (

                        return_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        return_id INTEGER NOT NULL,
                        sale_item_id INTEGER NOT NULL,
                        variant_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL
                            CHECK (quantity > 0),
                        unit_refund_amount INTEGER NOT NULL
                            CHECK (unit_refund_amount >= 0),
                        line_refund_amount INTEGER NOT NULL
                            CHECK (line_refund_amount >= 0),
                        restock INTEGER NOT NULL DEFAULT 1
                            CHECK (restock IN (0, 1)),
                        condition TEXT NOT NULL DEFAULT 'GOOD'
                            CHECK (
                                condition IN (
                                    'GOOD',
                                    'DAMAGED',
                                    'DEFECTIVE'
                                )
                            ),
                        notes TEXT,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (return_id)
                            REFERENCES sales_returns(return_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (sale_item_id)
                            REFERENCES sale_items(sale_item_id)
                            ON DELETE RESTRICT,

                        FOREIGN KEY (variant_id)
                            REFERENCES product_variants(variant_id)
                            ON DELETE RESTRICT
                    );


                    -- ==================================
                    -- INDEXES
                    -- ==================================

                    CREATE INDEX IF NOT EXISTS idx_products_category
                    ON products(category_id);

                    CREATE INDEX IF NOT EXISTS idx_products_name
                    ON products(product_name);

                    CREATE INDEX IF NOT EXISTS idx_products_active
                    ON products(is_active);

                    CREATE INDEX IF NOT EXISTS idx_variants_product
                    ON product_variants(product_id);

                    CREATE INDEX IF NOT EXISTS idx_variants_sku
                    ON product_variants(sku);

                    CREATE INDEX IF NOT EXISTS idx_variants_barcode
                    ON product_variants(barcode);

                    CREATE INDEX IF NOT EXISTS idx_inventory_transactions_variant
                    ON inventory_transactions(variant_id);

                    CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created_at
                    ON inventory_transactions(created_at);

                    CREATE INDEX IF NOT EXISTS idx_inventory_transactions_type
                    ON inventory_transactions(transaction_type);

                    CREATE INDEX IF NOT EXISTS idx_sales_customer
                    ON sales(customer_id);

                    CREATE INDEX IF NOT EXISTS idx_sales_cashier
                    ON sales(cashier_user_id);

                    CREATE INDEX IF NOT EXISTS idx_sales_created_at
                    ON sales(created_at);

                    CREATE INDEX IF NOT EXISTS idx_sales_status
                    ON sales(sale_status);

                    CREATE INDEX IF NOT EXISTS idx_sale_items_sale
                    ON sale_items(sale_id);

                    CREATE INDEX IF NOT EXISTS idx_sale_items_variant
                    ON sale_items(variant_id);

                    CREATE INDEX IF NOT EXISTS idx_payments_sale
                    ON payments(sale_id);

                    CREATE INDEX IF NOT EXISTS idx_payments_method
                    ON payments(payment_method);

                    CREATE INDEX IF NOT EXISTS idx_refunds_payment_id
                    ON refunds(payment_id);

                    CREATE INDEX IF NOT EXISTS idx_refunds_sale_id
                    ON refunds(sale_id);

                    CREATE INDEX IF NOT EXISTS idx_sales_returns_sale
                    ON sales_returns(sale_id);

                    CREATE INDEX IF NOT EXISTS idx_sales_returns_date
                    ON sales_returns(created_at);

                    CREATE INDEX IF NOT EXISTS idx_sales_return_items_return
                    ON sales_return_items(return_id);

                    CREATE INDEX IF NOT EXISTS idx_sales_return_items_sale_item
                    ON sales_return_items(sale_item_id);

                """)

                refund_columns = {
                    row["name"]
                    for row in connection.execute(
                        "PRAGMA table_info(refunds)"
                    ).fetchall()
                }

                if "return_id" not in refund_columns:
                    connection.execute("""
                        ALTER TABLE refunds
                        ADD COLUMN return_id INTEGER
                            REFERENCES sales_returns(return_id)
                            ON DELETE RESTRICT
                    """)

                category_columns = {
                    row["name"]
                    for row in connection.execute(
                        "PRAGMA table_info(categories)"
                    ).fetchall()
                }

                if "parent_category_id" not in category_columns:
                    connection.execute("""
                        ALTER TABLE categories
                        ADD COLUMN parent_category_id INTEGER
                            REFERENCES categories(category_id)
                            ON DELETE SET NULL
                    """)

        print("Database initialized successfully!")
        print(f"Database location: {DATABASE_PATH.resolve()}")

    # ==================================================
    # TRANSACTION MANAGEMENT
    # ==================================================

    @contextmanager
    def transaction(self):
        """
        Provide one shared SQLite transaction.

        All database operations using the yielded connection
        belong to the same transaction.
        """
        connection = self.connect()

        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ==================================================
    # DATABASE DEBUGGING
    # ==================================================

    def debug_connection(
        self,
        user_id: int | None = None
    ):
        """
        Display database information.

        Optionally inspect a specific user's roles.
        """

        with closing(self.connect()) as connection:

            print("\n========== DATABASE DEBUG ==========")

            # Database location
            print("\nDatabase location:")

            for row in connection.execute(
                "PRAGMA database_list"
            ).fetchall():

                print(dict(row))

            # Foreign key status
            print("\nForeign keys:")

            print(
                connection.execute(
                    "PRAGMA foreign_keys"
                ).fetchone()[0]
            )

            # Journal mode
            print("\nJournal mode:")

            print(
                connection.execute(
                    "PRAGMA journal_mode"
                ).fetchone()[0]
            )

            # Users
            print("\nUsers:")

            users = connection.execute("""
                SELECT
                    user_id,
                    username,
                    full_name,
                    is_active
                FROM users
                ORDER BY user_id
            """).fetchall()

            for row in users:
                print(dict(row))

            # Optional user role inspection
            if user_id is not None:

                print(f"\nRoles for user ID {user_id}:")

                roles = connection.execute("""
                    SELECT
                        u.username,
                        r.role_id,
                        r.role_name

                    FROM user_roles ur

                    INNER JOIN users u
                        ON ur.user_id = u.user_id

                    INNER JOIN roles r
                        ON ur.role_id = r.role_id

                    WHERE ur.user_id = ?

                """, (user_id,)).fetchall()

                for row in roles:
                    print(dict(row))

                print(f"\nPermissions for user ID {user_id}:")

                permissions = connection.execute("""
                    SELECT DISTINCT
                        p.permission_code

                    FROM user_roles ur

                    INNER JOIN role_permissions rp
                        ON ur.role_id = rp.role_id

                    INNER JOIN permissions p
                        ON rp.permission_id = p.permission_id

                    WHERE ur.user_id = ?

                    ORDER BY p.permission_code

                """, (user_id,)).fetchall()

                for row in permissions:
                    print(dict(row))

                print(
                    f"Total permissions: {len(permissions)}"
                )

            print("\n====================================\n")


# ==================================================
# DIRECT EXECUTION
# ==================================================

if __name__ == "__main__":

    database = Database()

    database.initialize()

    database.debug_connection()
