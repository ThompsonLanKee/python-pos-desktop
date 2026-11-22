
import sqlite3
from contextlib import closing
from typing import Any

from src.core.database import Database
from src.models import Product, ProductVariant
from src.repositories import (
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
)


class ProductService:
    """
    Handles product business logic.

    Features:
    - Create simple and variant-based products.
    - Automatically initialize inventory for each variant.
    - Retrieve products and their variants.
    - Search and filter products.
    - Update product information.
    - Activate and deactivate products.

    Product creation is handled within one database transaction.
    """

    def __init__(self, database: Database):
        self.database = database

        self.product_repository = ProductRepository(database)
        self.variant_repository = ProductVariantRepository(database)
        self.inventory_repository = InventoryRepository(database)

    # ==========================================
    # CREATE PRODUCT
    # ==========================================

    def create_product(
        self,
        product: Product,
        variants: list[dict[str, Any]]
    ) -> int:
        """
        Create a product, its variants, and inventory records.

        Required variant field:
            sku

        Optional variant fields:
            color_id
            size_id
            barcode
            cost_price
            selling_price
            is_active

        Simple products use None for color_id and size_id.

        Returns:
            Newly created product ID.
        """

        if not isinstance(product, Product):
            raise TypeError("product must be a Product instance.")

        if not isinstance(variants, list):
            raise TypeError("variants must be a list.")

        if not variants:
            raise ValueError(
                "A product must have at least one variant."
            )

        if product.category_id is None or product.category_id <= 0:
            raise ValueError("A valid category is required.")

        prepared_variants = []

        seen_skus = set()
        seen_barcodes = set()
        seen_combinations = set()

        # --------------------------------------
        # Validate variant input
        # --------------------------------------

        for specification in variants:

            if not isinstance(specification, dict):
                raise TypeError(
                    "Each variant specification must be a dictionary."
                )

            sku = specification.get("sku")

            if not isinstance(sku, str) or not sku.strip():
                raise ValueError(
                    "Every variant requires a valid SKU."
                )

            sku = sku.strip().upper()

            if sku in seen_skus:
                raise ValueError(
                    f"Duplicate SKU in request: {sku}"
                )

            seen_skus.add(sku)

            color_id = specification.get("color_id")
            size_id = specification.get("size_id")

            for field_name, field_value in (
                ("color_id", color_id),
                ("size_id", size_id)
            ):
                if field_value is not None:
                    if (
                        not isinstance(field_value, int)
                        or isinstance(field_value, bool)
                        or field_value <= 0
                    ):
                        raise ValueError(
                            f"{field_name} must be a positive integer or None."
                        )

            combination = (color_id, size_id)

            if combination in seen_combinations:
                raise ValueError(
                    "Duplicate color and size combination."
                )

            seen_combinations.add(combination)

            barcode = specification.get("barcode")

            if barcode is not None:
                if not isinstance(barcode, str):
                    raise TypeError("Barcode must be a string or None.")

                barcode = barcode.strip() or None

                if barcode is not None:
                    if barcode in seen_barcodes:
                        raise ValueError(
                            f"Duplicate barcode in request: {barcode}"
                        )

                    seen_barcodes.add(barcode)

            prepared_variants.append({
                "sku": sku,
                "color_id": color_id,
                "size_id": size_id,
                "barcode": barcode,
                "cost_price": specification.get("cost_price", 0),
                "selling_price": specification.get("selling_price", 0),
                "is_active": specification.get("is_active", 1),
            })

        # --------------------------------------
        # Create product and variants atomically
        # --------------------------------------

        try:
            with self.database.transaction() as connection:

                # 1. Validate category.

                category = connection.execute(
                    """
                    SELECT category_id
                    FROM categories
                    WHERE category_id = ?
                      AND is_active = 1
                    """,
                    (product.category_id,)
                ).fetchone()

                if category is None:
                    raise ValueError(
                        "Category does not exist or is inactive."
                    )

                # 2. Validate SKU, barcode, color, and size.

                for specification in prepared_variants:

                    sku = specification["sku"]
                    barcode = specification["barcode"]
                    color_id = specification["color_id"]
                    size_id = specification["size_id"]

                    existing_sku = connection.execute(
                        """
                        SELECT 1
                        FROM product_variants
                        WHERE sku = ? COLLATE NOCASE
                        LIMIT 1
                        """,
                        (sku,)
                    ).fetchone()

                    if existing_sku:
                        raise ValueError(
                            f"SKU already exists: {sku}"
                        )

                    if barcode is not None:

                        existing_barcode = connection.execute(
                            """
                            SELECT 1
                            FROM product_variants
                            WHERE barcode = ? COLLATE NOCASE
                            LIMIT 1
                            """,
                            (barcode,)
                        ).fetchone()

                        if existing_barcode:
                            raise ValueError(
                                f"Barcode already exists: {barcode}"
                            )

                    if color_id is not None:

                        color = connection.execute(
                            """
                            SELECT 1
                            FROM colors
                            WHERE color_id = ?
                              AND is_active = 1
                            """,
                            (color_id,)
                        ).fetchone()

                        if color is None:
                            raise ValueError(
                                f"Invalid or inactive color ID: {color_id}"
                            )

                    if size_id is not None:

                        size = connection.execute(
                            """
                            SELECT 1
                            FROM sizes
                            WHERE size_id = ?
                              AND is_active = 1
                            """,
                            (size_id,)
                        ).fetchone()

                        if size is None:
                            raise ValueError(
                                f"Invalid or inactive size ID: {size_id}"
                            )

                # 3. Create product.

                product_id = self.product_repository.create(
                    product,
                    connection=connection
                )

                # 4. Create variants and inventory.

                for specification in prepared_variants:

                    variant = ProductVariant(
                        product_id=product_id,
                        color_id=specification["color_id"],
                        size_id=specification["size_id"],
                        sku=specification["sku"],
                        barcode=specification["barcode"],
                        cost_price=specification["cost_price"],
                        selling_price=specification["selling_price"],
                        is_active=specification["is_active"],
                    )

                    variant_id = self.variant_repository.create(
                        variant,
                        connection=connection
                    )

                    self.inventory_repository.create(
                        variant_id,
                        connection=connection
                    )

                return product_id

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to create product due to a database constraint: {error}"
            ) from error

    # ==========================================
    # RETRIEVE PRODUCT DETAILS
    # ==========================================

    def get_product_details(
        self,
        product_id: int
    ) -> dict | None:
        """
        Retrieve a product with its category,
        variants, colors, sizes, and inventory.
        """

        if (
            not isinstance(product_id, int)
            or isinstance(product_id, bool)
            or product_id <= 0
        ):
            raise ValueError("Product ID must be a positive integer.")

        with closing(self.database.connect()) as connection:

            product_row = connection.execute(
                """
                SELECT
                    p.*,
                    c.category_name
                FROM products p
                INNER JOIN categories c
                    ON p.category_id = c.category_id
                WHERE p.product_id = ?
                """,
                (product_id,)
            ).fetchone()

            if product_row is None:
                return None

            variant_rows = connection.execute(
                """
                SELECT
                    pv.*,
                    col.color_name,
                    sz.size_name,
                    i.quantity_on_hand,
                    i.reorder_level
                FROM product_variants pv
                LEFT JOIN colors col
                    ON pv.color_id = col.color_id
                LEFT JOIN sizes sz
                    ON pv.size_id = sz.size_id
                LEFT JOIN inventory i
                    ON pv.variant_id = i.variant_id
                WHERE pv.product_id = ?
                ORDER BY pv.variant_id
                """,
                (product_id,)
            ).fetchall()

            return {
                "product": dict(product_row),
                "variants": [
                    dict(row) for row in variant_rows
                ]
            }

    # ==========================================
    # RETRIEVE ALL PRODUCTS
    # ==========================================

    def get_all_products(self) -> list[Product]:
        """Retrieve all products."""

        return self.product_repository.get_all()

    # ==========================================
    # RETRIEVE ACTIVE PRODUCTS
    # ==========================================

    def get_active_products(self) -> list[Product]:
        """Retrieve active products only."""

        return self.product_repository.get_active()

    # ==========================================
    # RETRIEVE PRODUCTS BY CATEGORY
    # ==========================================

    def get_products_by_category(
        self,
        category_id: int
    ) -> list[Product]:
        """Retrieve products belonging to a category."""

        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id <= 0
        ):
            raise ValueError(
                "Category ID must be a positive integer."
            )

        return self.product_repository.get_by_category(
            category_id
        )

    # ==========================================
    # SEARCH PRODUCTS
    # ==========================================

    def search_products(
        self,
        keyword: str
    ) -> list[Product]:
        """Search products by name or brand."""

        if not isinstance(keyword, str):
            raise TypeError("Search keyword must be a string.")

        keyword = keyword.strip()

        if not keyword:
            return self.get_all_products()

        return self.product_repository.search(keyword)

    # ==========================================
    # UPDATE PRODUCT
    # ==========================================

    def update_product(
        self,
        product: Product
    ) -> bool:
        """
        Update basic product information.

        Does not modify variants or inventory.
        """

        if not isinstance(product, Product):
            raise TypeError("product must be a Product instance.")

        if (
            product.product_id is None
            or product.product_id <= 0
        ):
            raise ValueError("A valid product ID is required.")

        if (
            product.category_id is None
            or product.category_id <= 0
        ):
            raise ValueError("A valid category is required.")

        with self.database.transaction() as connection:

            existing_product = connection.execute(
                """
                SELECT product_id
                FROM products
                WHERE product_id = ?
                """,
                (product.product_id,)
            ).fetchone()

            if existing_product is None:
                return False

            category = connection.execute(
                """
                SELECT category_id
                FROM categories
                WHERE category_id = ?
                  AND is_active = 1
                """,
                (product.category_id,)
            ).fetchone()

            if category is None:
                raise ValueError(
                    "Category does not exist or is inactive."
                )

            return self.product_repository.update(
                product,
                connection=connection
            )

    # ==========================================
    # PRODUCT STATUS MANAGEMENT
    # ==========================================

    def set_product_active(
        self,
        product_id: int,
        is_active: bool
    ) -> bool:
        """Activate or deactivate a product."""

        if (
            not isinstance(product_id, int)
            or isinstance(product_id, bool)
            or product_id <= 0
        ):
            raise ValueError(
                "Product ID must be a positive integer."
            )

        if not isinstance(is_active, bool):
            raise TypeError("is_active must be a boolean.")

        return self.product_repository.set_active(
            product_id,
            is_active
        )
