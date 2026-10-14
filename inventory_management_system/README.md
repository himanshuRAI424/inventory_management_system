# 📦 Inventory Management System (College Mini-Project)

A complete, lightweight, and modern **Inventory Management System** designed for academic evaluation, laboratory practical exams, and mini-project demonstrations.

---

## 🎯 1. Project Aim & Objectives

### **Aim**
To design and develop a web-based Inventory Management System that enables storekeepers and warehouse administrators to track, manage, update, and audit stock levels efficiently in real-time.

### **Objectives**
1. **Cataloging Products:** Maintain detailed records of products, including Unique Product Code, Name, Category, Quantity in Stock, and Unit Price.
2. **Preventing Out-of-Stock Situations:** Implement automated **Low-Stock Alerts** (threshold &le; 5 units) to notify managers when inventory needs replenishment.
3. **Data Integrity:** Enforce database constraints and backend validation rules (preventing negative quantities/prices and avoiding duplicate product IDs).
4. **Seamless User Experience:** Provide a Single-Page Application (SPA) feel with dynamic updates using the JavaScript Fetch API, eliminating full-page reloads on CRUD actions.
5. **Simplicity & Portability:** Keep architecture beginner-friendly and lightweight using Python's native SQLite3 database without requiring complex external database server setups.

---

## 💻 2. Technologies Used

| Layer | Technology | Rationale / Purpose |
|---|---|---|
| **Frontend UI** | **HTML5** | Semantic structure for dashboard KPI cards, forms, tables, and modal dialogs. |
| **Styling** | **CSS3** | Modern responsive design with custom CSS variables, flexbox, grid, animations, and toast badges. |
| **Client Scripting** | **Vanilla JavaScript (ES6+)** | Handles DOM events, form validations, search filtering, and asynchronous backend communication via Fetch API. |
| **Backend Framework** | **Python Flask (v3.x)** | Lightweight WSGI microframework handling HTTP routing, REST API endpoints, and error statuses. |
| **Database** | **SQLite3** | Zero-configuration, serverless, file-based relational database built into standard Python. |
| **Data Interchange** | **JSON (JavaScript Object Notation)** | Clean payload format for client-server communication. |

> **Note:** Strictly built **without** React, Node.js, MongoDB, or heavy ORMs, ensuring it is 100% compliant with university examination guidelines.

---

## 📂 3. Project Folder Structure

```text
inventory_management_system/
│
├── app.py                  # Core Flask backend server & REST API routes
├── inventory.db            # SQLite database file (auto-generated on launch)
├── requirements.txt        # Python dependency manifest (Flask)
├── run.bat                 # Convenient Windows 1-click launcher script
├── test_app.py             # Automated unit & integration test suite
├── README.md               # Complete project documentation & viva guide
│
├── templates/
│   └── index.html          # Frontend HTML5 single-page application layout
│
└── static/
    ├── style.css           # Custom modern CSS3 styling & responsive theme
    └── script.js           # Vanilla JavaScript for Fetch API, search & UI updates
```

---

## 🚀 4. Setup and Execution Instructions

### Prerequisites
- **Python 3.8+** installed on your computer.
- Python added to your system `PATH`.

### Step 1: Open the Project Directory
The project is saved directly on your **Desktop**:
```bash
cd "C:\Users\lenovo\Desktop\inventory_management_system"
```

### Step 2: Install Dependencies
Install Flask using pip:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
You can run it in two easy ways:

#### Option A: One-Click Launcher (Recommended for Windows)
Simply double-click the **`run.bat`** file located inside the project folder.

#### Option B: Terminal / Command Prompt
```bash
python app.py
```

### Step 4: Access the Dashboard
Open any web browser (Google Chrome, Microsoft Edge, Firefox) and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🗄️ 5. Database Schema

The database file `inventory.db` is managed by SQLite3. On startup, the `products` table is created automatically if it doesn't already exist.

### **Table: `products`**
```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    price REAL NOT NULL CHECK(price >= 0)
);
```

### **Column Descriptions & Constraints:**
- `id`: Internal autoincrementing primary key used for secure URL routing.
- `product_id`: User-defined inventory SKU or code (e.g., `PRD101`), enforced as **UNIQUE** and **NOT NULL**.
- `name`: Product title (e.g., `Wireless Mouse`), non-empty string.
- `category`: Classification tag (e.g., `Electronics`, `Stationery`, `Furniture`).
- `quantity`: Current stock count. Enforced by `CHECK(quantity >= 0)` to prevent negative inventory.
- `price`: Unit price. Enforced by `CHECK(price >= 0)` to prevent negative values.

---

## 🌐 6. REST API Endpoints & HTTP Methods

| Endpoint | Method | Description | Request Body (JSON) | Status Codes |
|---|---|---|---|---|
| `/` | `GET` | Serves the main HTML5 dashboard | None | `200 OK` |
| `/api/products` | `GET` | Fetches all products (supports `?search=` query) | None | `200 OK` |
| `/api/products/<id>` | `GET` | Retrieves a single product by primary key `id` | None | `200 OK`, `404 Not Found` |
| `/api/products` | `POST` | Inserts a new product into the database | `{"product_id", "name", "category", "quantity", "price"}` | `201 Created`, `400 Bad Request`, `409 Conflict` |
| `/api/products/<id>` | `PUT` | Updates existing product details | `{"product_id", "name", "category", "quantity", "price"}` | `200 OK`, `400 Bad Request`, `404 Not Found`, `409 Conflict` |
| `/api/products/<id>` | `DELETE` | Deletes a product from the database | None | `200 OK`, `404 Not Found` |

---

## 🔄 7. Detailed Explanation of CRUD Operations

### 1. **Create (C)**
- **User Action:** Fills out the "Add New Product" form and clicks "Save Product".
- **Frontend:** Validates data non-emptiness, confirms positive numbers, then issues an asynchronous `fetch('/api/products', { method: 'POST', body: JSON.stringify(...) })`.
- **Backend:** `add_product()` checks input constraints. Parameterized SQL query `INSERT INTO products ...` executes. If `product_id` already exists, an `IntegrityError` is intercepted, returning HTTP `409 Conflict`.
- **UI Update:** A success toast pops up, the form resets, and the table dynamically reloads without browser refresh.

### 2. **Read (R)**
- **Initial Load:** On page load (`DOMContentLoaded`), `loadProducts()` triggers `fetch('/api/products')`.
- **Search & Filter:** User types into the search box or picks a category. `applyFilters()` dynamically filters in JavaScript by `product_id`, `name`, or `category` and recalculates KPI metrics instantaneously.
- **Low Stock Filter:** Clicking the "Low Stock Only" button filters items whose quantity &le; 5.

### 3. **Update (U)**
- **User Action:** Clicks the "✏️ Edit" button next to any product row.
- **Frontend:** Opens a modal dialog populated with the current product's details.
- **Backend:** On submission, sends a `PUT /api/products/<id>` request. The server verifies the record exists, executes `UPDATE products SET ... WHERE id = ?`, and returns the updated product object.
- **UI Update:** The modal closes smoothly, toast alerts the user, and the table re-renders the updated details.

### 4. **Delete (D)**
- **User Action:** Clicks the "🗑️ Delete" button on a product row.
- **Safety Prompt:** A custom confirmation modal appears showing the product name and code.
- **Backend:** Once confirmed, sends a `DELETE /api/products/<id>`. The server executes `DELETE FROM products WHERE id = ?` and commits the change.
- **UI Update:** The deleted record is removed from the list, and KPIs update immediately.

---

## 🧪 8. Test Cases & Expected Results

An automated test script (`test_app.py`) is included to verify these scenarios:

| Test Case ID | Test Scenario | Input Data | Expected Status | Expected Result |
|---|---|---|---|---|
| **TC-01** | View Product Listing | `GET /api/products` | `200 OK` | Returns JSON array of all inventory items. |
| **TC-02** | Add Valid Product | Valid JSON payload (`PRD201`, `Desk Lamp`, `Furniture`, `10`, `799.00`) | `201 Created` | Product record created with new `id`. |
| **TC-03** | Duplicate Product ID | Re-submitting existing `product_id` | `409 Conflict` | Error: "Product ID already exists." |
| **TC-04** | Negative Quantity Validation | `quantity: -5` | `400 Bad Request` | Error: "Quantity must be a non-negative integer." |
| **TC-05** | Negative Price Validation | `price: -100` | `400 Bad Request` | Error: "Price must be a non-negative number." |
| **TC-06** | Missing Mandatory Fields | Missing `name` or `category` | `400 Bad Request` | Error: "Missing required field." |
| **TC-07** | Update Existing Product | `PUT /api/products/<id>` with updated name/qty | `200 OK` | Product updated in SQLite and returned in response. |
| **TC-08** | Delete Product | `DELETE /api/products/<id>` | `200 OK` | Product deleted; subsequent call returns `404 Not Found`. |
| **TC-09** | Dynamic Search | Query string: `?search=Mouse` | `200 OK` | Returns only products matching "Mouse". |
| **TC-10** | Low-Stock Calculation | Product with `quantity <= 5` | Displayed | Marked with "⚠️ Low Stock" badge and counted in KPI. |

### To Run the Automated Test Suite:
```bash
python test_app.py
```
*Expected Output:* `Ran 12 tests in ~0.20s ... OK (12/12 passed)`

---

## 🎓 9. College Practical / Viva Voce Questions & Answers

**Q1: Why did you choose SQLite over MySQL or MongoDB for this mini-project?**
> *Answer:* SQLite is a serverless, self-contained, zero-configuration database built directly into Python's standard library. It does not require hosting a separate database service, making the project portable and easy to run on any computer during a practical exam.

**Q2: What is the purpose of parameterized queries (`?`) in SQL statements?**
> *Answer:* Parameterized queries separate SQL code from user-supplied data, preventing **SQL Injection attacks**. The database engine treats parameters strictly as data values rather than executable code.

**Q3: How does the frontend communicate with the backend without reloading the page?**
> *Answer:* It uses the modern JavaScript **Fetch API**. Requests (`GET`, `POST`, `PUT`, `DELETE`) are sent asynchronously in the background. When the Flask server returns a JSON response, JavaScript manipulates the DOM dynamically to update the table and KPI cards.

**Q4: How is the Low-Stock Alert implemented?**
> *Answer:* The low-stock threshold is defined as 5 units. Both the JavaScript frontend and dashboard KPIs check if `quantity <= 5`. If true, the system renders a prominent amber warning badge and increments the "Low-Stock Alerts" counter.

**Q5: What HTTP status codes does the API return and why?**
> - `200 OK`: Successful retrieval, update, or deletion.
> - `201 Created`: Successful creation of a new product.
> - `400 Bad Request`: Validation failure (negative quantity, negative price, missing fields).
> - `404 Not Found`: Requested product ID does not exist in the database.
> - `409 Conflict`: Attempted insertion of a duplicate `product_id`.
> - `500 Internal Server Error`: Unhandled database or server exception.

---

## 👥 Authors & Academic Credits
- **Project Title:** Inventory Management System
- **Category:** Computer Science / Information Technology Mini-Project
- **Framework:** Python Flask & SQLite3
