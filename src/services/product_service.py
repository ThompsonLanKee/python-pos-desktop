
import sqlite3
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

    A product must have at least one variant.
    Every variant receives an inventory record.
    All creation operations use one database transaction.
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

        Each variant specification should contain:
            sku
            color_id
            size_id
            barcode
            cost_price
            selling_price
            is_active

        color_id and size_id can be None for simple products.

        Returns:
            The newly created product ID.
        """

        if not isinstance(product, Product):
            raise TypeError("product must be a Product instance.")

        if not variants:
            raise ValueError(
                "A product must have at least one variant."
            )

        if product.category_id is None or product.category_id <= 0:
            raise ValueError("A valid category is required.")

        if not isinstance(variants, list):
            raise TypeError("variants must be a list.")

        prepared_variants = []
        seen_skus = set()
        seen_combinations = set()

        # Validate the supplied variant specifications first.
        for specification in variants:

            if not isinstance(specification, dict):
                raise TypeError(
                    "Each variant specification must be a dictionary."
                )

            sku = specification.get("sku")

            if not isinstance(sku, str) or not sku.strip():
                raise ValueError("Every variant requires a SKU.")

            normalized_sku = sku.strip().upper()

            if normalized_sku in seen_skus:
                raise ValueError(
                    f"Duplicate SKU in request: {normalized_sku}"
                )

            seen_skus.add(normalized_sku)

            color_id = specification.get("color_id")
            size_id = specification.get("size_id")

            combination = (color_id, size_id)

            if combination in seen_combinations:
                raise ValueError(
                    "Duplicate color and size combination."
                )

            seen_combinations.add(combination)

            prepared_variants.append({
                "sku": normalized_sku,
                "color_id": color_id,
                "size_id": size_id,
                "barcode": specification.get("barcode"),
                "cost_price": specification.get("cost_price", 0),
                "selling_price": specification.get("selling_price", 0),
                "is_active": specification.get("is_active", 1),
            })

        # Create everything within one transaction.
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

                # 2. Validate every variant.
                for specification in prepared_variants:

                    color_id = specification["color_id"]
                    size_id = specification["size_id"]
                    sku = specification["sku"]

                    # Check SKU uniqueness.
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

                    # Check color.
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

                    # Check size.
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
