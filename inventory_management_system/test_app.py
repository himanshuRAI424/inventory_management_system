"""
Comprehensive Automated Test Suite for Inventory Management System
Validates all backend API endpoints, SQLite database operations, and validation rules.
"""

import unittest
import json
import os
import sqlite3
from app import app, init_db, DATABASE_PATH, get_db_connection


class TestInventoryManagementSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configure test client and initialize the database."""
        app.config["TESTING"] = True
        cls.client = app.test_client()
        init_db()

    def test_01_index_page(self):
        """Test GET / serves the frontend HTML interface."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Inventory Management System", response.data)
        print("  [PASS] GET / serves the main HTML dashboard.")

    def test_02_get_all_products(self):
        """Test GET /api/products returns products list."""
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("products"), list)
        self.assertGreater(len(data["products"]), 0)
        print(f"  [PASS] GET /api/products retrieved {len(data['products'])} products.")

    def test_03_add_valid_product(self):
        """Test POST /api/products creates a new product."""
        payload = {
            "product_id": "TEST_PRD_99",
            "name": "Testing Bluetooth Speaker",
            "category": "Audio",
            "quantity": 15,
            "price": 1999.99
        }
        response = self.client.post("/api/products", json=payload)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data.get("success"))
        self.assertEqual(data["product"]["product_id"], "TEST_PRD_99")
        self.assertEqual(data["product"]["name"], "Testing Bluetooth Speaker")
        self.assertEqual(data["product"]["quantity"], 15)
        self.assertEqual(data["product"]["price"], 1999.99)
        self.created_id = data["product"]["id"]
        print("  [PASS] POST /api/products successfully created product.")

    def test_04_duplicate_product_id(self):
        """Test POST /api/products rejects duplicate product_id with 409 Conflict."""
        # Try to insert duplicate of TEST_PRD_99
        payload = {
            "product_id": "TEST_PRD_99",
            "name": "Another Speaker",
            "category": "Audio",
            "quantity": 5,
            "price": 999.00
        }
        response = self.client.post("/api/products", json=payload)
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data.decode("utf-8"))
        self.assertFalse(data.get("success"))
        self.assertIn("already exists", data.get("error", ""))
        print("  [PASS] POST /api/products correctly caught duplicate product_id (409 Conflict).")

    def test_05_validation_negative_quantity(self):
        """Test POST /api/products rejects negative quantity with 400 Bad Request."""
        payload = {
            "product_id": "NEG_QTY_01",
            "name": "Invalid Item",
            "category": "Test",
            "quantity": -10,
            "price": 50.00
        }
        response = self.client.post("/api/products", json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode("utf-8"))
        self.assertFalse(data.get("success"))
        print("  [PASS] POST /api/products rejected negative quantity (400 Bad Request).")

    def test_06_validation_negative_price(self):
        """Test POST /api/products rejects negative price with 400 Bad Request."""
        payload = {
            "product_id": "NEG_PRICE_01",
            "name": "Invalid Item",
            "category": "Test",
            "quantity": 5,
            "price": -150.00
        }
        response = self.client.post("/api/products", json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode("utf-8"))
        self.assertFalse(data.get("success"))
        print("  [PASS] POST /api/products rejected negative price (400 Bad Request).")

    def test_07_validation_missing_fields(self):
        """Test POST /api/products rejects missing required fields with 400 Bad Request."""
        payload = {
            "product_id": "MISSING_01",
            "name": "Missing Category"
            # Missing category, quantity, price
        }
        response = self.client.post("/api/products", json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode("utf-8"))
        self.assertFalse(data.get("success"))
        print("  [PASS] POST /api/products rejected missing fields (400 Bad Request).")

    def test_08_get_single_product_and_not_found(self):
        """Test GET /api/products/<id> for existing and non-existent IDs."""
        # Non-existent ID
        response = self.client.get("/api/products/999999")
        self.assertEqual(response.status_code, 404)

        # Existing product
        all_res = self.client.get("/api/products")
        all_data = json.loads(all_res.data.decode("utf-8"))
        first_item = all_data["products"][0]
        first_id = first_item["id"]

        response = self.client.get(f"/api/products/{first_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["product"]["id"], first_id)
        print("  [PASS] GET /api/products/<id> handles existing and 404 correctly.")

    def test_09_update_product(self):
        """Test PUT /api/products/<id> updates existing product details."""
        # Find TEST_PRD_99
        all_res = self.client.get("/api/products?search=TEST_PRD_99")
        all_data = json.loads(all_res.data.decode("utf-8"))
        self.assertTrue(len(all_data["products"]) > 0)
        target = all_data["products"][0]
        target_id = target["id"]

        update_payload = {
            "product_id": "TEST_PRD_99",
            "name": "Testing Bluetooth Speaker (Upgraded)",
            "category": "Audio & Sound",
            "quantity": 3,  # Low stock test
            "price": 2499.50
        }
        response = self.client.put(f"/api/products/{target_id}", json=update_payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data.get("success"))
        self.assertEqual(data["product"]["name"], "Testing Bluetooth Speaker (Upgraded)")
        self.assertEqual(data["product"]["quantity"], 3)
        self.assertEqual(data["product"]["price"], 2499.50)
        print("  [PASS] PUT /api/products/<id> successfully updated product.")

    def test_10_search_filter(self):
        """Test GET /api/products?search=query searches correctly."""
        response = self.client.get("/api/products?search=Upgraded")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(len(data["products"]) >= 1)
        self.assertIn("Upgraded", data["products"][0]["name"])
        print("  [PASS] GET /api/products?search=... performs dynamic SQL search.")

    def test_11_delete_product(self):
        """Test DELETE /api/products/<id> deletes product and handles 404."""
        # Find TEST_PRD_99
        all_res = self.client.get("/api/products?search=TEST_PRD_99")
        all_data = json.loads(all_res.data.decode("utf-8"))
        target_id = all_data["products"][0]["id"]

        # Delete it
        del_response = self.client.delete(f"/api/products/{target_id}")
        self.assertEqual(del_response.status_code, 200)

        # Deleting again should return 404
        del_response_again = self.client.delete(f"/api/products/{target_id}")
        self.assertEqual(del_response_again.status_code, 404)
        print("  [PASS] DELETE /api/products/<id> deleted item and returns 404 on repeat.")

    def test_12_database_persistence(self):
        """Verify direct SQLite connection persists data."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)
        print(f"  [PASS] SQLite persistence verified ({count} records in inventory.db).")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RUNNING AUTOMATED TEST SUITE FOR INVENTORY MANAGEMENT SYSTEM")
    print("=" * 60 + "\n")
    unittest.main()
