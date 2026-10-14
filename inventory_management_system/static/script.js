/**
 * ========================================================
 * Inventory Management System - Frontend JavaScript
 * Vanilla JavaScript & Fetch API (No External Frameworks)
 * Designed for College Mini-Project / Viva Explanation
 * ========================================================
 */

// Application State
let allProducts = [];               // Master product list from backend
let isLowStockFilterActive = false; // Toggle state for low-stock filter
let pendingDeleteId = null;         // Product ID currently selected for deletion

// Low stock threshold constant (as per project requirements)
const LOW_STOCK_THRESHOLD = 5;

// DOM Elements
const productsTableBody = document.getElementById("products-table-body");
const tableLoading = document.getElementById("table-loading");
const tableEmpty = document.getElementById("table-empty");
const emptyTitle = document.getElementById("empty-title");
const emptyMessage = document.getElementById("empty-message");
const searchInput = document.getElementById("search-input");
const categoryFilter = document.getElementById("category-filter");
const lowStockFilterBtn = document.getElementById("low-stock-filter-btn");
const productCountBadge = document.getElementById("product-count-badge");

// KPI Elements
const kpiTotalProducts = document.getElementById("kpi-total-products");
const kpiTotalStock = document.getElementById("kpi-total-stock");
const kpiLowStock = document.getElementById("kpi-low-stock");
const kpiCategories = document.getElementById("kpi-categories");
const kpiCardLowStock = document.getElementById("kpi-card-low-stock");

// Forms & Modals
const addProductForm = document.getElementById("add-product-form");
const editProductForm = document.getElementById("edit-product-form");
const editModal = document.getElementById("edit-modal");
const deleteModal = document.getElementById("delete-modal");

// ========================================================
// 1. INITIALIZATION & LIFECYCLE
// ========================================================
document.addEventListener("DOMContentLoaded", () => {
    // Attach form submission listeners
    if (addProductForm) {
        addProductForm.addEventListener("submit", handleAddProduct);
    }
    if (editProductForm) {
        editProductForm.addEventListener("submit", handleEditProduct);
    }

    // Initial fetch of products from Flask API
    loadProducts();
});

// ========================================================
// 2. FETCH PRODUCTS (READ - GET /api/products)
// ========================================================
async function loadProducts() {
    showLoading(true);

    try {
        const response = await fetch("/api/products");
        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}: Failed to fetch products.`);
        }

        const data = await response.json();
        if (data.success && Array.isArray(data.products)) {
            allProducts = data.products;
            populateCategoryFilter();
            applyFilters();
            updateDashboardKPIs();
        } else {
            throw new Error(data.error || "Unexpected response format from server.");
        }
    } catch (error) {
        console.error("Error loading products:", error);
        showToast("Error Loading Products", error.message, "error");
        renderTableRows([]);
        showEmptyState(true, "Connection Error", "Could not connect to the Flask server. Please ensure the backend is running.");
    } finally {
        showLoading(false);
    }
}

// ========================================================
// 3. DASHBOARD METRICS / KPIS
// ========================================================
function updateDashboardKPIs() {
    // Total Products
    const totalCount = allProducts.length;
    kpiTotalProducts.textContent = totalCount;

    // Total Stock Quantity (sum of all quantities)
    const totalStock = allProducts.reduce((sum, p) => sum + (parseInt(p.quantity, 10) || 0), 0);
    kpiTotalStock.textContent = totalStock.toLocaleString();

    // Low-Stock Count (quantity <= LOW_STOCK_THRESHOLD)
    const lowStockCount = allProducts.filter(p => parseInt(p.quantity, 10) <= LOW_STOCK_THRESHOLD).length;
    kpiLowStock.textContent = lowStockCount;

    // Unique Categories Count
    const uniqueCategories = new Set(allProducts.map(p => (p.category || "").trim().toLowerCase()).filter(Boolean));
    kpiCategories.textContent = uniqueCategories.size;

    // Highlight low-stock card if any item is low on stock
    if (lowStockCount > 0) {
        kpiCardLowStock.style.borderColor = "var(--warning)";
    } else {
        kpiCardLowStock.style.borderColor = "var(--border-color)";
    }
}

// ========================================================
// 4. ADD PRODUCT (CREATE - POST /api/products)
// ========================================================
async function handleAddProduct(event) {
    event.preventDefault();

    // Extract values
    const productIdInput = document.getElementById("product_id");
    const nameInput = document.getElementById("name");
    const categoryInput = document.getElementById("category");
    const quantityInput = document.getElementById("quantity");
    const priceInput = document.getElementById("price");

    const payload = {
        product_id: productIdInput.value.trim(),
        name: nameInput.value.trim(),
        category: categoryInput.value.trim(),
        quantity: quantityInput.value.trim(),
        price: priceInput.value.trim()
    };

    // Client-side Validation
    if (!payload.product_id || !payload.name || !payload.category || payload.quantity === "" || payload.price === "") {
        showToast("Validation Error", "All fields marked with * are required.", "warning");
        return;
    }

    const qtyNumber = Number(payload.quantity);
    if (!Number.isInteger(qtyNumber) || qtyNumber < 0) {
        showToast("Validation Error", "Quantity must be a non-negative whole integer (0 or greater).", "warning");
        quantityInput.focus();
        return;
    }

    const priceNumber = Number(payload.price);
    if (isNaN(priceNumber) || priceNumber < 0) {
        showToast("Validation Error", "Price must be a non-negative number (0 or greater).", "warning");
        priceInput.focus();
        return;
    }

    const submitBtn = document.getElementById("add-product-btn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving...";

    try {
        const response = await fetch("/api/products", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_id: payload.product_id,
                name: payload.name,
                category: payload.category,
                quantity: qtyNumber,
                price: priceNumber
            })
        });

        const result = await response.json();

        if (response.status === 201 && result.success) {
            showToast("Success", result.message || "Product added successfully!", "success");
            resetAddForm();
            // Refresh inventory and KPIs from database
            await loadProducts();
        } else {
            // Handle error (e.g., 409 Conflict for duplicate ID, 400 Bad Request)
            showToast("Failed to Add Product", result.error || "An error occurred.", "error");
        }
    } catch (error) {
        console.error("Error adding product:", error);
        showToast("Network Error", "Could not reach the server to save the product.", "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Save Product";
    }
}

function resetAddForm() {
    addProductForm.reset();
}

function scrollToAddProduct() {
    const panel = document.getElementById("add-product-panel");
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
    document.getElementById("product_id").focus();
}

// ========================================================
// 5. EDIT & UPDATE PRODUCT (UPDATE - PUT /api/products/<id>)
// ========================================================
function openEditModal(id) {
    const product = allProducts.find(p => p.id === id);
    if (!product) {
        showToast("Error", "Product details could not be found.", "error");
        return;
    }

    // Populate modal inputs
    document.getElementById("edit-db-id").value = product.id;
    document.getElementById("edit-product-id").value = product.product_id;
    document.getElementById("edit-name").value = product.name;
    document.getElementById("edit-category").value = product.category;
    document.getElementById("edit-quantity").value = product.quantity;
    document.getElementById("edit-price").value = product.price;

    editModal.style.display = "flex";
}

function closeEditModal() {
    editModal.style.display = "none";
    editProductForm.reset();
}

async function handleEditProduct(event) {
    event.preventDefault();

    const dbId = document.getElementById("edit-db-id").value;
    const productId = document.getElementById("edit-product-id").value.trim();
    const name = document.getElementById("edit-name").value.trim();
    const category = document.getElementById("edit-category").value.trim();
    const rawQty = document.getElementById("edit-quantity").value.trim();
    const rawPrice = document.getElementById("edit-price").value.trim();

    // Client-side Validation
    if (!productId || !name || !category || rawQty === "" || rawPrice === "") {
        showToast("Validation Error", "All fields are required.", "warning");
        return;
    }

    const qty = Number(rawQty);
    if (!Number.isInteger(qty) || qty < 0) {
        showToast("Validation Error", "Quantity must be a non-negative whole integer.", "warning");
        return;
    }

    const price = Number(rawPrice);
    if (isNaN(price) || price < 0) {
        showToast("Validation Error", "Price must be a non-negative number.", "warning");
        return;
    }

    const saveBtn = document.getElementById("save-edit-btn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Updating...";

    try {
        const response = await fetch(`/api/products/${dbId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_id: productId,
                name: name,
                category: category,
                quantity: qty,
                price: price
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast("Success", result.message || "Product updated successfully!", "success");
            closeEditModal();
            // Refresh table dynamically without reloading the page
            await loadProducts();
        } else {
            showToast("Update Failed", result.error || "Could not update product.", "error");
        }
    } catch (error) {
        console.error("Error updating product:", error);
        showToast("Network Error", "Could not reach the server to update the product.", "error");
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Changes";
    }
}

// ========================================================
// 6. DELETE PRODUCT (DELETE - DELETE /api/products/<id>)
// ========================================================
function openDeleteModal(id, name, code) {
    pendingDeleteId = id;
    document.getElementById("delete-product-name").textContent = name;
    document.getElementById("delete-product-id-label").textContent = code;
    deleteModal.style.display = "flex";
}

function closeDeleteModal() {
    deleteModal.style.display = "none";
    pendingDeleteId = null;
}

async function executeDeleteProduct() {
    if (!pendingDeleteId) return;

    const confirmBtn = document.getElementById("confirm-delete-btn");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";

    try {
        const response = await fetch(`/api/products/${pendingDeleteId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast("Deleted", result.message || "Product removed from inventory.", "info");
            closeDeleteModal();
            // Refresh table dynamically
            await loadProducts();
        } else {
            showToast("Delete Failed", result.error || "Could not delete product.", "error");
        }
    } catch (error) {
        console.error("Error deleting product:", error);
        showToast("Network Error", "Failed to communicate with the server.", "error");
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Yes, Delete";
    }
}

// ========================================================
// 7. SEARCH & FILTERING (DYNAMIC, NO PAGE RELOAD)
// ========================================================
function handleSearchInput() {
    applyFilters();
}

function clearSearch() {
    searchInput.value = "";
    applyFilters();
    searchInput.focus();
}

function toggleLowStockFilter() {
    isLowStockFilterActive = !isLowStockFilterActive;
    updateLowStockButtonState();
    applyFilters();
}

function filterByLowStockToggle() {
    isLowStockFilterActive = !isLowStockFilterActive;
    updateLowStockButtonState();
    applyFilters();
}

function updateLowStockButtonState() {
    if (isLowStockFilterActive) {
        lowStockFilterBtn.classList.add("active-low-stock");
        kpiCardLowStock.classList.add("active-filter");
        lowStockFilterBtn.textContent = "⚠️ Showing Low Stock (Clear)";
    } else {
        lowStockFilterBtn.classList.remove("active-low-stock");
        kpiCardLowStock.classList.remove("active-filter");
        lowStockFilterBtn.textContent = "⚠️ Low Stock Only";
    }
}

function applyFilters() {
    const query = searchInput.value.trim().toLowerCase();
    const selectedCategory = categoryFilter.value.trim().toLowerCase();

    const filtered = allProducts.filter(product => {
        // Search across Product ID, Name, and Category
        const matchesQuery = !query || 
            (product.product_id && product.product_id.toLowerCase().includes(query)) ||
            (product.name && product.name.toLowerCase().includes(query)) ||
            (product.category && product.category.toLowerCase().includes(query));

        // Category filter
        const matchesCategory = !selectedCategory || 
            (product.category && product.category.toLowerCase() === selectedCategory);

        // Low stock filter (<= 5)
        const matchesLowStock = !isLowStockFilterActive || 
            (parseInt(product.quantity, 10) <= LOW_STOCK_THRESHOLD);

        return matchesQuery && matchesCategory && matchesLowStock;
    });

    renderTableRows(filtered);

    // Update count badge
    productCountBadge.textContent = `${filtered.length} of ${allProducts.length} Products`;

    // Show empty state if filtered list is empty
    if (filtered.length === 0) {
        if (allProducts.length === 0) {
            showEmptyState(true, "Inventory is Empty", "No products have been added yet. Use the 'Add New Product' form to get started.");
        } else {
            showEmptyState(true, "No Matching Products", "No inventory items match your current search or filter criteria.");
        }
    } else {
        showEmptyState(false);
    }
}

// ========================================================
// 8. RENDER TABLE ROWS & STATUS BADGES
// ========================================================
function renderTableRows(products) {
    productsTableBody.innerHTML = "";

    products.forEach(product => {
        const qty = parseInt(product.quantity, 10);
        const price = parseFloat(product.price);
        const totalValue = (qty * price).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        // Determine stock status and badge
        let statusBadge = "";
        let rowClass = "";

        if (qty === 0) {
            statusBadge = `<span class="badge badge-danger">Out of Stock</span>`;
            rowClass = "row-out-of-stock";
        } else if (qty <= LOW_STOCK_THRESHOLD) {
            statusBadge = `<span class="badge badge-warning">⚠️ Low Stock (${qty})</span>`;
            rowClass = "row-low-stock";
        } else {
            statusBadge = `<span class="badge badge-success">In Stock</span>`;
        }

        const tr = document.createElement("tr");
        if (rowClass) tr.className = rowClass;

        tr.innerHTML = `
            <td>
                <span class="product-code-pill">${escapeHTML(product.product_id)}</span>
            </td>
            <td>
                <strong>${escapeHTML(product.name)}</strong>
            </td>
            <td>
                <span class="category-tag">${escapeHTML(product.category)}</span>
            </td>
            <td>
                <span class="quantity-badge">${qty}</span>
            </td>
            <td>
                ₹${price.toFixed(2)}
            </td>
            <td>
                ₹${totalValue}
            </td>
            <td>
                ${statusBadge}
            </td>
            <td class="text-center">
                <div class="table-actions">
                    <button 
                        class="btn btn-sm btn-edit" 
                        title="Edit Product"
                        onclick="openEditModal(${product.id})"
                    >
                        ✏️ Edit
                    </button>
                    <button 
                        class="btn btn-sm btn-delete" 
                        title="Delete Product"
                        onclick="openDeleteModal(${product.id}, '${escapeQuote(product.name)}', '${escapeQuote(product.product_id)}')"
                    >
                        🗑️ Delete
                    </button>
                </div>
            </td>
        `;

        productsTableBody.appendChild(tr);
    });
}

function populateCategoryFilter() {
    const currentVal = categoryFilter.value;
    const categories = Array.from(
        new Set(allProducts.map(p => (p.category || "").trim()).filter(Boolean))
    ).sort();

    categoryFilter.innerHTML = `<option value="">All Categories</option>`;
    categories.forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        if (cat === currentVal) option.selected = true;
        categoryFilter.appendChild(option);
    });
}

// ========================================================
// 9. UI HELPERS (LOADING, EMPTY STATE, TOASTS, MODALS)
// ========================================================
function showLoading(isLoading) {
    tableLoading.style.display = isLoading ? "block" : "none";
    if (isLoading) {
        tableEmpty.style.display = "none";
    }
}

function showEmptyState(show, title = "No Products Found", message = "") {
    if (show) {
        emptyTitle.textContent = title;
        emptyMessage.textContent = message;
        tableEmpty.style.display = "block";
    } else {
        tableEmpty.style.display = "none";
    }
}

function closeModalOnBackdrop(event, modalId) {
    if (event.target.id === modalId) {
        if (modalId === "edit-modal") closeEditModal();
        if (modalId === "delete-modal") closeDeleteModal();
    }
}

// Toast notification function
function showToast(title, message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    const iconMap = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️"
    };

    toast.innerHTML = `
        <span class="toast-icon">${iconMap[type] || "ℹ️"}</span>
        <div class="toast-content">
            <div class="toast-title">${escapeHTML(title)}</div>
            <div class="toast-desc">${escapeHTML(message)}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);

    // Auto-remove toast after 4 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            toast.style.opacity = "0";
            toast.style.transform = "translateX(50%)";
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// Safety sanitizers for HTML output
function escapeHTML(str) {
    if (!str && str !== 0) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeQuote(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
