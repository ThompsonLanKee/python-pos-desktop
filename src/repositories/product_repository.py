from typing import Optional

from src.models import Product, ProductVariant
from src.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):

    def create(self, product: Product) -> int:
        query = """
            INSERT INTO products (
                product_name,
                description,
                category_id,
                brand,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    product.product_name,
                    product.description,
                    product.category_id,
                    product.brand,
                    int(product.is_active)
                )
            )
            return cursor.lastrowid

    def get_by_id(self, product_id: int) -> Optional[Product]:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM products
                WHERE product_id = ?
                """,
                (product_id,)
            ).fetchone()
            return self._to_product(row) if row else None

    def get_all(
        self,
        category_id: Optional[int] = None,
        active_only: bool = False
    ) -> list[Product]:
        query = "SELECT * FROM products WHERE 1 = 1"
        parameters = []

        if category_id is not None:
            query += " AND category_id = ?"
            parameters.append(category_id)

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY product_name COLLATE NOCASE"

        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
            return [self._to_product(row) for row in rows]

    def update(self, product: Product) -> bool:
        if product.product_id is None:
            raise ValueError("Product ID is required.")

        query = """
            UPDATE products
            SET product_name = ?,
                description = ?,
                category_id = ?,
                brand = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    product.product_name,
                    product.description,
                    product.category_id,
                    product.brand,
                    int(product.is_active),
                    product.product_id
                )
            )
            return cursor.rowcount > 0

    def set_active(self, product_id: int, is_active: bool) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE products
                SET is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
                """,
                (int(is_active), product_id)
            )
            return cursor.rowcount > 0

    def delete(self, product_id: int) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM products WHERE product_id = ?",
                (product_id,)
            )
            return cursor.rowcount > 0

    def create_variant(self, variant: ProductVariant) -> int:
        query = """
            INSERT INTO product_variants (
                product_id,
                sku,
                barcode,
                color_id,
                size_id,
                cost_price,
                selling_price,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    variant.product_id,
                    variant.sku,
                    variant.barcode,
                    variant.color_id,
                    variant.size_id,
                    variant.cost_price,
                    variant.selling_price,
                    int(variant.is_active)
                )
            )
            return cursor.lastrowid

    def get_variant_by_id(
        self,
        variant_id: int
    ) -> Optional[ProductVariant]:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM product_variants
                WHERE variant_id = ?
                """,
                (variant_id,)
            ).fetchone()
            return self._to_variant(row) if row else None

    def get_variant_by_sku(self, sku: str) -> Optional[ProductVariant]:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM product_variants
                WHERE sku = ? COLLATE NOCASE
                """,
                (sku.strip(),)
            ).fetchone()
            return self._to_variant(row) if row else None

    def get_variants(
        self,
        product_id: int,
        active_only: bool = False
    ) -> list[ProductVariant]:
        query = """
            SELECT *
            FROM product_variants
            WHERE product_id = ?
        """
        parameters = [product_id]

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY variant_id"

        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
            return [self._to_variant(row) for row in rows]

    def update_variant(self, variant: ProductVariant) -> bool:
        if variant.variant_id is None:
            raise ValueError("Variant ID is required.")

        query = """
            UPDATE product_variants
            SET sku = ?,
                barcode = ?,
                color_id = ?,
                size_id = ?,
                cost_price = ?,
                selling_price = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE variant_id = ?
        """

        with self.connection() as connection:
            cursor = connection.execute(
                query,
                (
                    variant.sku,
                    variant.barcode,
                    variant.color_id,
                    variant.size_id,
                    variant.cost_price,
                    variant.selling_price,
                    int(variant.is_active),
                    variant.variant_id
                )
            )
            return cursor.rowcount > 0

    def delete_variant(self, variant_id: int) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM product_variants WHERE variant_id = ?",
                (variant_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def _to_product(row) -> Product:
        data = dict(row)
        data["is_active"] = bool(data["is_active"])
        return Product(**data)

    @staticmethod
    def _to_variant(row) -> ProductVariant:
        data = dict(row)
        data["is_active"] = bool(data["is_active"])
        return ProductVariant(**data)