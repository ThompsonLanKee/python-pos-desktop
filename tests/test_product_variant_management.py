import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.core.database as database_module
from src.core.database import Database
from src.models import Category, Color, Product, Size
from src.repositories import (
    CategoryRepository,
    ColorRepository,
    InventoryRepository,
    ProductVariantRepository,
    SizeRepository,
)
from src.services.product_service import ProductService


class ProductVariantManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "test.db"
        self.database_path_patch = patch.object(
            database_module, "DATABASE_PATH", database_path
        )
        self.database_path_patch.start()

        self.database = Database()
        self.database.initialize()
        self.service = ProductService(self.database)
        category_id = CategoryRepository(self.database).create(
            Category(category_name="Variant Management")
        )
        self.product_id = self.service.create_product(
            Product(
                product_name="Variant Management Product",
                category_id=category_id,
            ),
            [{"sku": "BASE-SKU"}],
        )

    def tearDown(self):
        self.database_path_patch.stop()
        self.temporary_directory.cleanup()

    def test_variant_options_and_lifecycle(self):
        color_repository = ColorRepository(self.database)
        size_repository = SizeRepository(self.database)

        blue_id = color_repository.create(
            Color(color_name="Blue", hex_code="#0000FF")
        )
        inactive_color_id = color_repository.create(
            Color(color_name="Inactive", is_active=False)
        )
        size_l_id = size_repository.create(Size(size_name="L", sort_order=2))
        size_s_id = size_repository.create(Size(size_name="S", sort_order=1))

        options = self.service.get_variant_options()
        self.assertEqual(
            [color["color_id"] for color in options["colors"]],
            [blue_id],
        )
        self.assertEqual(
            [size["size_id"] for size in options["sizes"]],
            [size_s_id, size_l_id],
        )

        specification = {
            "sku": " blue-l ",
            "barcode": " 12345 ",
            "color_id": blue_id,
            "size_id": size_l_id,
            "cost_price": 10,
            "selling_price": 15,
        }
        variant_id = self.service.create_variant(self.product_id, specification)

        inventory = InventoryRepository(self.database).get_by_variant(variant_id)
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory["quantity_on_hand"], 0)

        with self.assertRaisesRegex(ValueError, "combination already exists"):
            self.service.create_variant(
                self.product_id,
                {
                    **specification,
                    "sku": "ANOTHER-SKU",
                    "barcode": None,
                },
            )
        with self.assertRaisesRegex(ValueError, "inactive"):
            self.service.create_variant(
                self.product_id,
                {
                    **specification,
                    "sku": "INACTIVE-COLOR-SKU",
                    "color_id": inactive_color_id,
                    "barcode": None,
                },
            )

        updated = {
            **specification,
            "sku": " BLUE-L-UPDATED ",
            "cost_price": 12,
            "selling_price": 18,
        }
        self.assertTrue(self.service.update_variant(variant_id, updated))
        saved_variant = ProductVariantRepository(self.database).get_by_id(variant_id)
        self.assertIsNotNone(saved_variant)
        self.assertEqual(saved_variant.sku, "BLUE-L-UPDATED")
        self.assertEqual(saved_variant.selling_price, 18)

        self.assertTrue(self.service.set_variant_active(variant_id, False))
        saved_variant = ProductVariantRepository(self.database).get_by_id(variant_id)
        self.assertFalse(saved_variant.is_active)

    def test_create_variant_rolls_back_if_inventory_creation_fails(self):
        color_id = ColorRepository(self.database).create(
            Color(color_name="Rollback Color")
        )
        size_id = SizeRepository(self.database).create(
            Size(size_name="Rollback Size")
        )
        with patch.object(
            self.service.inventory_repository,
            "create",
            side_effect=sqlite3.IntegrityError("inventory failure"),
        ):
            with self.assertRaisesRegex(ValueError, "Unable to create variant"):
                self.service.create_variant(
                    self.product_id,
                    {
                        "sku": "ROLLBACK-SKU",
                        "color_id": color_id,
                        "size_id": size_id,
                    },
                )

        self.assertIsNone(
            ProductVariantRepository(self.database).get_by_sku("ROLLBACK-SKU")
        )


if __name__ == "__main__":
    unittest.main()
