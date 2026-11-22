
import sqlite3

from src.core.database import Database
from src.models import ProductVariant
from src.repositories import (
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
)


class ProductVariantService:
    """
    Handles product variant business logic.

    Each variant belongs to one product and has
    its own SKU, price, and inventory record.
    """

    def __init__(self, database: Database):

        self.database = database

        self.product_repository = ProductRepository(database)
        self.variant_repository = ProductVariantRepository(database)
        self.inventory_repository = InventoryRepository(database)

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def _validate_product(
        self,
        connection,
        product_id: int
    ) -> None:
        """Ensure the parent product exists and is active."""

        product = connection.execute(
            """
            SELECT product_id
            FROM products
            WHERE product_id = ?
              AND is_active = 1
            """,
            (product_id,)
        ).fetchone()

        if product is None:
            raise ValueError(
                "Product does not exist or is inactive."
            )

    def _validate_attributes(
        self,
        connection,
        color_id: int | None,
        size_id: int | None
    ) -> None:
        """Validate optional color and size references."""

        if color_id is not None:

            color = connection.execute(
                """
                SELECT color_id
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
                SELECT size_id
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

    def _validate_unique_values(
        self,
        connection,
        sku: str,
        barcode: str | None,
        product_id: int,
        color_id: int | None,
        size_id: int | None,
        exclude_variant_id: int | None = None
    ) -> None:
        """Validate SKU, barcode, and variant combination uniqueness."""

        # SKU uniqueness.
        query = """
            SELECT 1
            FROM product_variants
            WHERE sku = ? COLLATE NOCASE
        """
        parameters = [sku]

        if exclude_variant_id is not None:
            query += " AND variant_id != ?"
            parameters.append(exclude_variant_id)

        if connection.execute(
            query,
            parameters
        ).fetchone():
            raise ValueError(f"SKU already exists: {sku}")

        # Barcode uniqueness.
        if barcode is not None:

            query = """
                SELECT 1
                FROM product_variants
                WHERE barcode = ? COLLATE NOCASE
            """
            parameters = [barcode]

            if exclude_variant_id is not None:
                query += " AND variant_id != ?"
                parameters.append(exclude_variant_id)

            if connection.execute(
                query,
                parameters
            ).fetchone():
                raise ValueError(
                    f"Barcode already exists: {barcode}"
                )

        # Combination uniqueness within the same product.
        query = """
            SELECT 1
            FROM product_variants
            WHERE product_id = ?
              AND color_id IS ?
              AND size_id IS ?
        """
        parameters = [
            product_id,
            color_id,
            size_id
        ]

        if exclude_variant_id is not None:
            query += " AND variant_id != ?"
            parameters.append(exclude_variant_id)

        if connection.execute(
            query,
            parameters
        ).fetchone():
            raise ValueError(
                "This product already has the same color and size combination."
            )

    # ==========================================
    # ADD VARIANT
    # ==========================================

    def add_variant(
        self,
        variant: ProductVariant
    ) -> int:
        """
        Add a variant to an existing product.

        Automatically creates its inventory record.

        Returns:
            Newly created variant ID.
        """

        if not isinstance(variant, ProductVariant):
            raise TypeError(
                "variant must be a ProductVariant instance."
            )

        if variant.product_id is None or variant.product_id <= 0:
            raise ValueError("A valid product ID is required.")

        if not variant.sku:
            raise ValueError("SKU is required.")

        try:
            with self.database.transaction() as connection:

                self._validate_product(
                    connection,
                    variant.product_id
                )

                self._validate_attributes(
                    connection,
                    variant.color_id,
                    variant.size_id
                )

                self._validate_unique_values(
                    connection,
                    variant.sku,
                    variant.barcode,
                    variant.product_id,
                    variant.color_id,
                    variant.size_id
                )

                variant_id = self.variant_repository.create(
                    variant,
                    connection=connection
                )

                self.inventory_repository.create(
                    variant_id,
                    connection=connection
                )

                return variant_id

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to add variant: {error}"
            ) from error

    # ==========================================
    # RETRIEVE VARIANT BY ID
    # ==========================================

    def get_variant_by_id(
        self,
        variant_id: int
    ) -> ProductVariant | None:

        if variant_id <= 0:
            raise ValueError("Variant ID must be positive.")

        return self.variant_repository.get_by_id(variant_id)

    # ==========================================
    # RETRIEVE VARIANTS BY PRODUCT
    # ==========================================

    def get_variants_by_product(
        self,
        product_id: int
    ) -> list[ProductVariant]:

        if product_id <= 0:
            raise ValueError("Product ID must be positive.")

        return self.variant_repository.get_by_product(
            product_id
        )

    # ==========================================
    # RETRIEVE VARIANT BY SKU
    # ==========================================

    def get_variant_by_sku(
        self,
        sku: str
    ) -> ProductVariant | None:

        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("A valid SKU is required.")

        return self.variant_repository.get_by_sku(
            sku.strip()
        )

    # ==========================================
    # RETRIEVE VARIANT BY BARCODE
    # ==========================================

    def get_variant_by_barcode(
        self,
        barcode: str
    ) -> ProductVariant | None:

        if not isinstance(barcode, str) or not barcode.strip():
            raise ValueError("A valid barcode is required.")

        return self.variant_repository.get_by_barcode(
            barcode.strip()
        )

    # ==========================================
    # RETRIEVE ALL VARIANTS
    # ==========================================

    def get_all_variants(self) -> list[ProductVariant]:

        return self.variant_repository.get_all()

    # ==========================================
    # UPDATE VARIANT
    # ==========================================

    def update_variant(
        self,
        variant: ProductVariant
    ) -> bool:
        """
        Update SKU, barcode, color, size, and prices.

        Product ownership cannot be changed here.
        """

        if not isinstance(variant, ProductVariant):
            raise TypeError(
                "variant must be a ProductVariant instance."
            )

        if variant.variant_id is None or variant.variant_id <= 0:
            raise ValueError("A valid variant ID is required.")

        try:
            with self.database.transaction() as connection:

                existing = connection.execute(
                    """
                    SELECT product_id
                    FROM product_variants
                    WHERE variant_id = ?
                    """,
                    (variant.variant_id,)
                ).fetchone()

                if existing is None:
                    return False

                self._validate_attributes(
                    connection,
                    variant.color_id,
                    variant.size_id
                )

                self._validate_unique_values(
                    connection,
                    variant.sku,
                    variant.barcode,
                    existing["product_id"],
                    variant.color_id,
                    variant.size_id,
                    exclude_variant_id=variant.variant_id
                )

                return self.variant_repository.update(
                    variant,
                    connection=connection
                )

        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"Unable to update variant: {error}"
            ) from error

    # ==========================================
    # VARIANT STATUS MANAGEMENT
    # ==========================================

    def set_variant_active(
        self,
        variant_id: int,
        is_active: bool
    ) -> bool:
        """Activate or deactivate an individual variant."""

        if variant_id <= 0:
            raise ValueError("Variant ID must be positive.")

        if not isinstance(is_active, bool):
            raise TypeError("is_active must be a boolean.")

        return self.variant_repository.set_active(
            variant_id,
            is_active
        )
