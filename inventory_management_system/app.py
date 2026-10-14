"""
Inventory Management System
Backend Application using Flask and SQLite3
Designed for College Mini-Project / Practical Examination
"""

import os
import sqlite3
from flask import Flask, request, jsonify, render_template

# Initialize Flask Application
app = Flask(__name__)

# Database file path (located in the same directory as app.py)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "inventory.db")


def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Row factory is set to sqlite3.Row so columns can be accessed by name.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes the SQLite database and creates the 'products' table if it does not exist.
    Also pre-populates a few initial products if the database is brand new.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the products table with strict constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price REAL NOT NULL CHECK(price >= 0)
        );
    """)

    # Check if table is empty; if so, insert a few sample products for easy demonstration
    cursor.execute("SELECT COUNT(*) FROM products;")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_products = [
            ("PRD101", "Wireless Optical Mouse", "Electronics", 18, 599.00),
            ("PRD102", "Mechanical Gaming Keyboard", "Electronics", 4, 2499.00),  # Low stock (<= 5)
            ("PRD103", "Ergonomic Office Chair", "Furniture", 8, 7499.50),
            ("PRD104", "USB-C Fast Charging Cable", "Accessories", 3, 299.00),     # Low stock (<= 5)
            ("PRD105", "27-inch IPS Monitor", "Electronics", 12, 14999.00),
            ("PRD106", "Spiral Notebook (Pack of 5)", "Stationery", 2, 350.00)     # Low stock (<= 5)
        ]
        cursor.executemany("""
            INSERT INTO products (product_id, name, category, quantity, price)
            VALUES (?, ?, ?, ?, ?);
        """, sample_products)
        conn.commit()

    conn.commit()
    conn.close()


def validate_product_data(data):
    """
    Validates input product data received from frontend.
    Returns: (is_valid: bool, error_message: str or None, sanitized_data: dict or None)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a valid JSON object.", None

    # Required field checks
    required_fields = ["product_id", "name", "category", "quantity", "price"]
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: '{field}'.", None

    # String field validations
    product_id = str(data.get("product_id", "")).strip()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()

    if not product_id:
        return False, "Product ID cannot be blank.", None
    if not name:
        return False, "Product Name cannot be blank.", None
    if not category:
        return False, "Category cannot be blank.", None

    # Quantity validation (must be non-negative integer)
    raw_qty = data.get("quantity")
    if isinstance(raw_qty, bool):
        return False, "Quantity must be an integer, not a boolean.", None
    try:
        # Check if it represents an integer without fractional parts
        qty_float = float(raw_qty)
        if not qty_float.is_integer():
            return False, "Quantity must be a whole integer.", None
        quantity = int(qty_float)
        if quantity < 0:
            return False, "Quantity must be a non-negative integer (0 or greater).", None
    except (ValueError, TypeError):
        return False, "Quantity must be a valid number.", None

    # Price validation (must be non-negative number)
    raw_price = data.get("price")
    if isinstance(raw_price, bool):
        return False, "Price must be a number, not a boolean.", None
    try:
        price = float(raw_price)
        if price < 0:
            return False, "Price must be a non-negative number (0.00 or greater).", None
        price = round(price, 2)
    except (ValueError, TypeError):
        return False, "Price must be a valid numerical value.", None

    sanitized = {
        "product_id": product_id,
        "name": name,
        "category": category,
        "quantity": quantity,
        "price": price
    }
    return True, None, sanitized


# ==========================================
# Frontend Route
# ==========================================
@app.route("/")
def index():
    """Serves the single-page HTML interface."""
    return render_template("index.html")


# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/products", methods=["GET"])
def get_all_products():
    """
    Fetch all products from the SQLite database.
    Optional query parameter:
      - search: filter by product_id, name, or category
    Returns: JSON list of products with status 200.
    """
    search_query = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        # Parameterized search across product_id, name, or category (case-insensitive in SQLite LIKE)
        sql = """
            SELECT id, product_id, name, category, quantity, price
            FROM products
            WHERE product_id LIKE ? OR name LIKE ? OR category LIKE ?
            ORDER BY id DESC;
        """
        wildcard = f"%{search_query}%"
        cursor.execute(sql, (wildcard, wildcard, wildcard))
    else:
        cursor.execute("""
            SELECT id, product_id, name, category, quantity, price
            FROM products
            ORDER BY id DESC;
        """)

    rows = cursor.fetchall()
    conn.close()

    # Convert SQLite Rows to dictionary list
    products = [
        {
            "id": row["id"],
            "product_id": row["product_id"],
            "name": row["name"],
            "category": row["category"],
            "quantity": row["quantity"],
            "price": row["price"]
        }
        for row in rows
    ]

    return jsonify({"success": True, "count": len(products), "products": products}), 200


@app.route("/api/products/<int:id>", methods=["GET"])
def get_single_product(id):
    """
    Fetch a single product by its database primary key (id).
    Returns: JSON product object or 404 if not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, product_id, name, category, quantity, price
        FROM products
        WHERE id = ?;
    """, (id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"success": False, "error": f"Product with ID #{id} was not found."}), 404

    product = {
        "id": row["id"],
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category"],
        "quantity": row["quantity"],
        "price": row["price"]
    }

    return jsonify({"success": True, "product": product}), 200


@app.route("/api/products", methods=["POST"])
def add_product():
    """
    Add a new product to the database.
    Validates all fields and prevents duplicate product_id.
    Returns: 201 Created on success, 400 or 409 on error.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request. JSON body is required."}), 400

    is_valid, err_msg, sanitized = validate_product_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO products (product_id, name, category, quantity, price)
            VALUES (?, ?, ?, ?, ?);
        """, (
            sanitized["product_id"],
            sanitized["name"],
            sanitized["category"],
            sanitized["quantity"],
            sanitized["price"]
        ))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError as e:
        conn.close()
        # Handle unique constraint violation for product_id
        if "UNIQUE constraint failed: products.product_id" in str(e):
            return jsonify({
                "success": False,
                "error": f"Product ID '{sanitized['product_id']}' already exists. Please choose a unique ID."
            }), 409
        return jsonify({"success": False, "error": f"Database integrity violation: {str(e)}"}), 400
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

    # Fetch created row
    cursor.execute("SELECT id, product_id, name, category, quantity, price FROM products WHERE id = ?;", (new_id,))
    row = cursor.fetchone()
    conn.close()

    created_product = {
        "id": row["id"],
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category"],
        "quantity": row["quantity"],
        "price": row["price"]
    }

    return jsonify({
        "success": True,
        "message": f"Product '{created_product['name']}' added successfully!",
        "product": created_product
    }), 201


@app.route("/api/products/<int:id>", methods=["PUT"])
def update_product(id):
    """
    Update an existing product's details.
    Returns: 200 OK on success, 400/404/409 on error.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request. JSON body is required."}), 400

    is_valid, err_msg, sanitized = validate_product_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if target product exists
    cursor.execute("SELECT id FROM products WHERE id = ?;", (id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        return jsonify({"success": False, "error": f"Product with ID #{id} does not exist."}), 404

    try:
        cursor.execute("""
            UPDATE products
            SET product_id = ?, name = ?, category = ?, quantity = ?, price = ?
            WHERE id = ?;
        """, (
            sanitized["product_id"],
            sanitized["name"],
            sanitized["category"],
            sanitized["quantity"],
            sanitized["price"],
            id
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        if "UNIQUE constraint failed: products.product_id" in str(e):
            return jsonify({
                "success": False,
                "error": f"Product ID '{sanitized['product_id']}' is already used by another product."
            }), 409
        return jsonify({"success": False, "error": f"Database integrity violation: {str(e)}"}), 400
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

    # Fetch updated row
    cursor.execute("SELECT id, product_id, name, category, quantity, price FROM products WHERE id = ?;", (id,))
    row = cursor.fetchone()
    conn.close()

    updated_product = {
        "id": row["id"],
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category"],
        "quantity": row["quantity"],
        "price": row["price"]
    }

    return jsonify({
        "success": True,
        "message": f"Product '{updated_product['name']}' updated successfully!",
        "product": updated_product
    }), 200


@app.route("/api/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    """
    Delete a product from the database by its primary key ID.
    Returns: 200 OK on success, 404 if product does not exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify existence
    cursor.execute("SELECT id, name, product_id FROM products WHERE id = ?;", (id,))
    target = cursor.fetchone()

    if target is None:
        conn.close()
        return jsonify({"success": False, "error": f"Cannot delete. Product with ID #{id} was not found."}), 404

    product_name = target["name"]
    product_code = target["product_id"]

    cursor.execute("DELETE FROM products WHERE id = ?;", (id,))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Product '{product_name}' ({product_code}) has been deleted successfully."
    }), 200


# Fallback error handlers returning JSON
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"success": False, "error": "Endpoint not found."}), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({"success": False, "error": "HTTP Method not allowed for this endpoint."}), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"success": False, "error": "Internal server error occurred."}), 500


if __name__ == "__main__":
    # Initialize the database on startup
    init_db()
    print("=" * 60)
    print("  Inventory Management System (College Mini-Project)")
    print("  Server is starting up on http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
