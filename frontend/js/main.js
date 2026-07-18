/**
 * ================================================
 * F and B POULTRY FARM LIMITED - Main JavaScript
 * ================================================
 * This file handles ALL the shared functionality:
 * - API calls to the backend
 * - Login/Logout logic
 * - Navigation (showing correct menu based on role)
 * - Cart management
 */

// ==========================================
// CONFIGURATION
// ==========================================
const API_BASE_URL = 'http://localhost:5000/api';

// ==========================================
// HELPER: Make API calls
// ==========================================
async function apiCall(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('token');
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    // Add authorization token if logged in
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add body data for POST/PUT requests
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Something went wrong');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==========================================
// AUTHENTICATION
// ==========================================

// Register a new customer
async function registerUser(username, email, password, phone) {
    const result = await apiCall('/register', 'POST', {
        username: username,
        email: email,
        password: password,
        phone: phone
    });
    
    // Show verification modal if verification code is provided
    if (result.verification_code) {
        showVerificationModal(result.user_id, result.verification_code);
    }
    
    return result;
}

// Show verification modal
function showVerificationModal(userId, code) {
    document.getElementById('verify-user-id').value = userId;
    document.getElementById('verification-code').value = code;
    document.getElementById('verify-modal').classList.add('active');
}

// Verify account with code
async function verifyAccount(userId, code) {
    const result = await apiCall('/verify-account', 'POST', {
        user_id: userId,
        code: code
    });
    return result;
}

// Login user
async function loginUser(email, password) {
    const result = await apiCall('/login', 'POST', {
        email: email,
        password: password
    });
    
    // Save token and user info to browser storage
    localStorage.setItem('token', result.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    
    return result;
}

// Logout user
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/index.html';
}

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('token') !== null;
}

// Get current user info
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Check if current user is admin
function isAdmin() {
    const user = getCurrentUser();
    return user && user.role === 'admin';
}

// ==========================================
// NAVIGATION
// ==========================================

// Update navigation bar based on login status
function updateNavbar() {
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;
    
    const user = getCurrentUser();
    
    if (isLoggedIn()) {
        if (user.role === 'admin') {
            // Admin Navigation
            navLinks.innerHTML = `
                <li><a href="/index.html">Home</a></li>
                <li><a href="/pages/admin-dashboard.html">Dashboard</a></li>
                <li><a href="/pages/admin-products.html">Products</a></li>
                <li><a href="/pages/admin-orders.html">Orders</a></li>
                <li><a href="/pages/admin-customers.html">Customers</a></li>
                <li><a href="/pages/admin-ads.html">Adverts</a></li>
                <li><a href="#" onclick="logout()">Logout (${user.username})</a></li>
            `;
        } else {
            // Customer Navigation
            navLinks.innerHTML = `
                <li><a href="/index.html">Home</a></li>
                <li><a href="/pages/products.html">Products</a></li>
                <li><a href="/pages/customer-dashboard.html">My Orders</a></li>
                <li><a href="/pages/order-history.html">History</a></li>
                <li><a href="#" onclick="showCart()">Cart</a></li>
                <li><a href="#" onclick="logout()">Logout (${user.username})</a></li>
            `;
        }
    } else {
        // Guest Navigation
        navLinks.innerHTML = `
            <li><a href="/index.html">Home</a></li>
            <li><a href="/pages/products.html">Products</a></li>
            <li><a href="/pages/login.html">Login</a></li>
            <li><a href="/pages/register.html">Register</a></li>
        `;
    }
}

// Mobile menu toggle
function toggleMenu() {
    const navLinks = document.getElementById('nav-links');
    navLinks.classList.toggle('active');
}

// ==========================================
// CART MANAGEMENT
// ==========================================

// Show cart sidebar
function showCart() {
    const cartSidebar = document.getElementById('cart-sidebar');
    if (cartSidebar) {
        cartSidebar.classList.add('active');
        loadCart();
    } else {
        alert('Please go to the Products page to view your cart');
    }
}

// Close cart sidebar
function closeCart() {
    const cartSidebar = document.getElementById('cart-sidebar');
    if (cartSidebar) {
        cartSidebar.classList.remove('active');
    }
}

// Load cart items
async function loadCart() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const cartCount = document.getElementById('cart-count');
    
    if (!cartItems) return;
    
    try {
        const items = await apiCall('/cart');
        
        // Update cart count badge
        if (cartCount) {
            const totalQty = items.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalQty;
            cartCount.style.display = totalQty > 0 ? 'inline' : 'none';
        }
        
        if (items.length === 0) {
            cartItems.innerHTML = '<p style="text-align:center;color:#888;">Your cart is empty</p>';
            if (cartTotal) cartTotal.textContent = 'Total: GHS 0.00';
            return;
        }
        
        let html = '';
        let total = 0;
        
        items.forEach(item => {
            total += item.subtotal;
            html += `
                <div class="cart-item">
                    <div>
                        <strong>${item.product_name}</strong>
                        <br>
                        <small>GHS ${item.price} x ${item.quantity}</small>
                    </div>
                    <div>
                        <strong>GHS ${item.subtotal}</strong>
                        <br>
                        <button onclick="removeFromCart(${item.id})" class="btn btn-danger btn-small">Remove</button>
                    </div>
                </div>
            `;
        });
        
        cartItems.innerHTML = html;
        if (cartTotal) cartTotal.textContent = `Total: GHS ${total.toFixed(2)}`;
        
    } catch (error) {
        cartItems.innerHTML = '<p style="text-align:center;color:#d32f2f;">Error loading cart</p>';
    }
}

// Add item to cart
async function addToCart(productId, quantity = 1) {
    if (!isLoggedIn()) {
        alert('Please login first to add items to cart');
        window.location.href = '/pages/login.html';
        return;
    }
    
    try {
        await apiCall('/cart', 'POST', {
            product_id: productId,
            quantity: quantity
        });
        
        alert('Added to cart!');
        loadCart(); // Refresh cart
    } catch (error) {
        alert('Error adding to cart: ' + error.message);
    }
}

// Remove item from cart
async function removeFromCart(itemId) {
    try {
        await apiCall(`/cart/${itemId}`, 'DELETE');
        loadCart(); // Refresh cart display
    } catch (error) {
        alert('Error removing item');
    }
}

// Clear entire cart
async function clearCart() {
    if (!confirm('Clear your cart?')) return;
    
    try {
        await apiCall('/cart/clear', 'DELETE');
        loadCart();
    } catch (error) {
        alert('Error clearing cart');
    }
}

// ==========================================
// PAGE INITIALIZATION
// ==========================================

// Run when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Update navigation
    updateNavbar();
    
    // Load cart count if logged in
    if (isLoggedIn()) {
        loadCart();
    }
});

