"""
MAIN FLASK APPLICATION for F and B Poultry Farm Limited
======================================================
This is the main server file. It handles ALL API requests from the frontend.
Think of it as the "receptionist" that receives requests and sends back responses.

How to run: python main.py
The server will start at: http://localhost:5000
"""

import os
import random
import json
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS  # Allows frontend to talk to backend
from flask_bcrypt import Bcrypt  # For password encryption
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Product, Order, OrderItem, Payment, Advertisement, Cart

# ----- CREATE THE FLASK APP -----
app = Flask(__name__)

# Allow requests from any website (for development)
CORS(app)

# ----- CONFIGURATION -----
# Database location (SQLite file will be created in the backend folder)
basedir = Path(__file__).resolve().parent
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{basedir / "database.db"}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for JWT tokens (in production, use a real secret)
app.config['JWT_SECRET_KEY'] = 'f-and-b-poultry-farm-secret-key-2024'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
app.config['JWT_CSRF_CHECK_FORM'] = False
app.config['JWT_CSRF_IN_COOKIES'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def admin_required():
    """Check if the current user is an admin"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return False
    return True


# ============================================================
# AUTHENTICATION ENDPOINTS (Login & Register)
# ============================================================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new customer account with verification"""
    data = request.get_json()
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Generate 6-digit verification code
    verification_code = str(random.randint(100000, 999999))
    
    # Encrypt the password before saving
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Create new user (not verified yet)
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role='customer',
        phone=data.get('phone', ''),
        is_verified=False,
        verification_code=verification_code
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # TODO: Send verification code via email/SMS in production
    # For now, return it in the response for testing
    
    return jsonify({
        'message': 'Account created! Please verify your account.',
        'user': new_user.to_dict(),
        'verification_code': verification_code,  # Remove this in production!
        'user_id': new_user.id
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Login user with verification check"""
    data = request.get_json()
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password matches
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check if user is verified (skip verification for admin)
    if not user.is_verified and user.role != 'admin':
        return jsonify({
            'error': 'Account not verified. Please verify your email/phone first.',
            'needs_verification': True,
            'user_id': user.id
        }), 403
    
    # Create JWT token (like a digital ID card)
    token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200


# ============================================================
# PRODUCT ENDPOINTS
# ============================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products (filter by category if specified)"""
    category = request.args.get('category')
    
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    
    return jsonify([p.to_dict() for p in products]), 200


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(product.to_dict()), 200


@app.route('/api/products', methods=['POST'])
@jwt_required()
def add_product():
    """Add a new product (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    new_product = Product(
        name=data['name'],
        category=data['category'],
        price=data['price'],
        stock_quantity=data['stock_quantity'],
        description=data.get('description', ''),
        image_url=data.get('image_url', '')
    )
    
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({'message': 'Product added!', 'product': new_product.to_dict()}), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update a product (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    
    # Update only the fields that were provided
    if 'name' in data:
        product.name = data['name']
    if 'category' in data:
        product.category = data['category']
    if 'price' in data:
        product.price = data['price']
    if 'stock_quantity' in data:
        product.stock_quantity = data['stock_quantity']
    if 'description' in data:
        product.description = data['description']
    if 'image_url' in data:
        product.image_url = data['image_url']
    
    db.session.commit()
    
    return jsonify({'message': 'Product updated!', 'product': product.to_dict()}), 200


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Product deleted!'}), 200


# ============================================================
# CART ENDPOINTS
# ============================================================

@app.route('/api/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """Get all items in the current user's cart"""
    customer_id = get_jwt_identity()
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    
    return jsonify([item.to_dict() for item in cart_items]), 200


@app.route('/api/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add an item to the cart"""
    customer_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if product exists
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Check if product already in cart
    existing_item = Cart.query.filter_by(
        customer_id=customer_id,
        product_id=data['product_id']
    ).first()
    
    if existing_item:
        # Update quantity if already in cart
        existing_item.quantity += data.get('quantity', 1)
    else:
        # Add new item to cart
        cart_item = Cart(
            customer_id=customer_id,
            product_id=data['product_id'],
            quantity=data.get('quantity', 1)
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({'message': 'Added to cart!'}), 201


@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    """Remove an item from the cart"""
    customer_id = get_jwt_identity()
    cart_item = Cart.query.filter_by(id=item_id, customer_id=customer_id).first()
    
    if not cart_item:
        return jsonify({'error': 'Item not found in cart'}), 404
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'message': 'Removed from cart!'}), 200


@app.route('/api/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear all items from the cart"""
    customer_id = get_jwt_identity()
    Cart.query.filter_by(customer_id=customer_id).delete()
    db.session.commit()
    
    return jsonify({'message': 'Cart cleared!'}), 200


# ============================================================
# ORDER ENDPOINTS
# ============================================================

@app.route('/api/orders', methods=['POST'])
@jwt_required()
def place_order():
    """Place a new order from cart items"""
    customer_id = get_jwt_identity()
    
    # Get all cart items
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total amount
    total_amount = sum(item.product.price * item.quantity for item in cart_items if item.product)
    
    # Create the order
    new_order = Order(
        customer_id=customer_id,
        total_amount=total_amount,
        status='pending'
    )
    db.session.add(new_order)
    db.session.flush()  # Get the order ID before committing
    
    # Add each cart item as an order item
    for cart_item in cart_items:
        if cart_item.product:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # Reduce stock
            cart_item.product.stock_quantity -= cart_item.quantity
    
    # Clear the cart
    Cart.query.filter_by(customer_id=customer_id).delete()
    
    db.session.commit()
    
    return jsonify({'message': 'Order placed!', 'order': new_order.to_dict()}), 201


@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get orders - Admin gets all, Customers get their own"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if user.role == 'admin':
        # Admin can see all orders
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        # Customers see only their orders
        orders = Order.query.filter_by(customer_id=current_user_id)\
                           .order_by(Order.order_date.desc()).all()
    
    return jsonify([order.to_dict() for order in orders]), 200


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get a single order by ID"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Check if user has permission
    if user.role != 'admin' and order.customer_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(order.to_dict()), 200


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    
    return jsonify({'message': 'Order status updated!', 'order': order.to_dict()}), 200


# ============================================================
# PAYMENT ENDPOINTS
# ============================================================

@app.route('/api/payments', methods=['POST'])
@jwt_required()
def make_payment():
    """Process payment for an order (simulated)"""
    customer_id = get_jwt_identity()
    data = request.get_json()
    
    order = Order.query.get(data['order_id'])
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Check if order belongs to this customer
    if order.customer_id != customer_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if already paid
    existing_payment = Payment.query.filter_by(order_id=order.id).first()
    if existing_payment:
        return jsonify({'error': 'Order already paid'}), 400
    
    # Simulate payment processing (always succeeds)
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method=data.get('payment_method', 'simulated'),
        payment_status='completed'
    )
    
    db.session.add(payment)
    order.status = 'confirmed'  # Auto-confirm on payment
    db.session.commit()
    
    return jsonify({'message': 'Payment successful!', 'payment': payment.to_dict()}), 201


# ============================================================
# CUSTOMER MANAGEMENT (Admin)
# ============================================================

@app.route('/api/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Get all customers (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    customers = User.query.filter_by(role='customer').all()
    return jsonify([c.to_dict() for c in customers]), 200


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """Delete a customer (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    customer = User.query.get(customer_id)
    if not customer or customer.role != 'customer':
        return jsonify({'error': 'Customer not found'}), 404
    
    db.session.delete(customer)
    db.session.commit()
    
    return jsonify({'message': 'Customer deleted!'}), 200


# ============================================================
# ADVERTISEMENT ENDPOINTS
# ============================================================

@app.route('/api/ads', methods=['GET'])
def get_ads():
    """Get all advertisements"""
    ads = Advertisement.query.order_by(Advertisement.created_at.desc()).all()
    return jsonify([ad.to_dict() for ad in ads]), 200


@app.route('/api/ads', methods=['POST'])
@jwt_required()
def create_ad():
    """Create a new advertisement (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    new_ad = Advertisement(
        title=data['title'],
        content=data['content'],
        image_url=data.get('image_url', ''),
        posted_by=current_user_id
    )
    
    db.session.add(new_ad)
    db.session.commit()
    
    return jsonify({'message': 'Advertisement posted!', 'ad': new_ad.to_dict()}), 201


@app.route('/api/ads/<int:ad_id>', methods=['DELETE'])
@jwt_required()
def delete_ad(ad_id):
    """Delete an advertisement (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    db.session.delete(ad)
    db.session.commit()
    
    return jsonify({'message': 'Advertisement deleted!'}), 200


# ============================================================
# DASHBOARD STATS
# ============================================================

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get dashboard statistics (Admin only)"""
    if not admin_required():
        return jsonify({'error': 'Admin access required'}), 403
    
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    total_revenue = db.session.query(db.func.sum(Payment.amount))\
                              .filter(Payment.payment_status == 'completed').scalar() or 0
    
    # Get orders by status
    pending_orders = Order.query.filter_by(status='pending').count()
    confirmed_orders = Order.query.filter_by(status='confirmed').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    
    return jsonify({
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders
    }), 200


# ============================================================
# VERIFICATION ENDPOINT
# ============================================================

@app.route('/api/verify-account', methods=['POST'])
def verify_account():
    """Verify user account with verification code"""
    data = request.get_json()
    
    user = User.query.get(data['user_id'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.verification_code != data['code']:
        return jsonify({'error': 'Invalid verification code'}), 400
    
    # Mark user as verified
    user.is_verified = True
    user.verification_code = None  # Clear the code after use
    db.session.commit()
    
    return jsonify({
        'message': 'Account verified successfully! You can now login.',
        'user': user.to_dict()
    }), 200


# ============================================================
# PAYSTACK PAYMENT INTEGRATION
# ============================================================

@app.route('/api/paystack/initialize', methods=['POST'])
@jwt_required()
def initialize_paystack_payment():
    """Initialize payment with Paystack"""
    data = request.get_json()
    customer_id = get_jwt_identity()
    
    order = Order.query.get(data['order_id'])
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if order.customer_id != customer_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # TODO: Integrate with real Paystack API
    # For now, return simulated payment URL
    
    return jsonify({
        'status': True,
        'message': 'Payment initialized',
        'data': {
            'authorization_url': f'http://localhost:3000/pay?order_id={order.id}&amount={order.total_amount}',
            'reference': f'PAY-{order.id}-{random.randint(1000, 9999)}',
            'amount': order.total_amount
        }
    }), 200


@app.route('/api/paystack/verify', methods=['GET'])
@jwt_required()
def verify_paystack_payment():
    """Verify Paystack payment"""
    customer_id = get_jwt_identity()
    reference = request.args.get('reference')
    
    # TODO: Verify with real Paystack API
    # For now, simulate successful payment
    
    order_id = int(reference.split('-')[1])
    order = Order.query.get(order_id)
    
    if not order or order.customer_id != customer_id:
        return jsonify({'error': 'Order not found'}), 404
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method='paystack',
        payment_status='completed'
    )
    db.session.add(payment)
    order.status = 'confirmed'
    db.session.commit()
    
    return jsonify({
        'status': True,
        'message': 'Payment verified successfully!',
        'data': payment.to_dict()
    }), 200


# ============================================================
# SIMPLE PAYMENT SYSTEM (No Paystack needed for testing)
# ============================================================

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """Create a new Mobile Money payment (simulated)"""
    data = request.get_json()
    
    # Generate unique reference
    reference = f"MM-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}"
    
    # Get mobile money details
    phone = data.get('phone', '')
    provider = data.get('provider', 'mtn')
    
    # Map provider codes to full names
    provider_names = {
        'mtn': 'MTN Mobile Money',
        'vodafone': 'Vodafone Cash',
        'airteltigo': 'AirtelTigo Money'
    }
    
    # Save payment to JSON file
    payment_data = {
        'reference': reference,
        'name': data.get('name'),
        'email': data.get('email'),
        'phone': phone,
        'provider': provider_names.get(provider, provider),
        'amount': data.get('amount'),
        'status': 'pending',
        'paymentMethod': 'mobile_money',
        'receiver': 'F and B Poultry Farm Limited',
        'receiverPhone': '0530043569',  # Your business phone for receiving payments
        'createdAt': datetime.now().isoformat(),
        'paidAt': None
    }
    
    # Read existing payments
    try:
        with open('payments.json', 'r') as f:
            payments = json.load(f)
    except:
        payments = []
    
    payments.append(payment_data)
    
    # Save back to file
    with open('payments.json', 'w') as f:
        json.dump(payments, f, indent=2)
    
    # Return simulated payment URL
    return jsonify({
        'status': True,
        'message': 'Mobile Money payment initialized',
        'data': {
            'authorization_url': f'/pages/simulate-payment.html?reference={reference}&amount={data.get("amount")}&phone={phone}&provider={provider}',
            'reference': reference,
            'amount': data.get('amount'),
            'phone': phone,
            'provider': provider_names.get(provider, provider)
        }
    }), 200


@app.route('/api/simulate-payment', methods=['POST'])
def simulate_payment():
    """Simulate a successful payment"""
    data = request.get_json()
    reference = data.get('reference')
    
    # Read payments
    try:
        with open('payments.json', 'r') as f:
            payments = json.load(f)
    except:
        return jsonify({'status': False, 'message': 'Payment not found'}), 404
    
    # Find and update payment
    payment_found = False
    for payment in payments:
        if payment['reference'] == reference:
            payment['status'] = 'success'
            payment['paidAt'] = datetime.now().isoformat()
            payment_found = True
            break
    
    if not payment_found:
        return jsonify({'status': False, 'message': 'Payment not found'}), 404
    
    # Save back to file
    with open('payments.json', 'w') as f:
        json.dump(payments, f, indent=2)
    
    return jsonify({
        'status': True,
        'message': 'Payment simulated successfully!',
        'data': {
            'reference': reference,
            'status': 'success'
        }
    }), 200


@app.route('/api/verify-payment', methods=['GET'])
def verify_payment():
    """Verify payment status"""
    reference = request.args.get('reference')
    
    # Read payments
    try:
        with open('payments.json', 'r') as f:
            payments = json.load(f)
    except:
        return jsonify({'status': False, 'message': 'Payment not found'}), 404
    
    # Find payment
    payment = None
    for p in payments:
        if p['reference'] == reference:
            payment = p
            break
    
    if not payment:
        return jsonify({'status': False, 'message': 'Payment not found'}), 404
    
    return jsonify({
        'status': True,
        'message': 'Payment verified',
        'data': payment
    }), 200


# ============================================================
# USER INFO ENDPOINT
# ============================================================

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get the currently logged-in user's information"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


# ============================================================
# SERVE FRONTEND STATIC FILES
# ============================================================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')
PAGES_DIR = os.path.join(FRONTEND_DIR, 'pages')

def no_cache(response):
    """Disable browser caching"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def serve_index():
    """Serve the main HTML page"""
    return no_cache(send_from_directory(FRONTEND_DIR, 'index.html'))

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files from frontend/css/"""
    return no_cache(send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename))

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JS files from frontend/js/"""
    return no_cache(send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename))

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    """Serve HTML page files from frontend/pages/"""
    return no_cache(send_from_directory(PAGES_DIR, filename))

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any other static files from frontend root"""
    return no_cache(send_from_directory(FRONTEND_DIR, filename))


# ============================================================
# CREATE DATABASE TABLES & RUN SERVER
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("[OK] Database tables created successfully!")
        
        # Check if admin user exists, if not create one
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin_password = bcrypt.generate_password_hash('Hector1234').decode('utf-8')
            admin = User(
                username='Douglas Yeboah',
                email='douglasyeboah633@mail.com',
                password_hash=admin_password,
                role='admin',
                phone='054411993',
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("[OK] Default admin created: douglasyeboah633@mail.com / Hector1234")
    
    print("\n" + "="*50)
    print("F and B Poultry Farm Limited")
    print("Server running at: http://localhost:5000")
    print("Admin login: douglasyeboah633@mail.com / Hector1234")
    print("="*50 + "\n")
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask server
    app.run(host='0.0.0.0', port=port)
