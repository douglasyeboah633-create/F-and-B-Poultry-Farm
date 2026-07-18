"""
DATABASE MODELS for F and B Poultry Farm Limited
===============================================
This file defines the structure of our database tables.
Think of each class as a "blueprint" for a table in the database.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create a database object - this will connect Python to SQLite
db = SQLAlchemy()


class User(db.Model):
    """Table to store all users (Admin and Customers)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)           # Unique ID for each user
    username = db.Column(db.String(80), unique=True, nullable=False)  # Username (must be unique)
    email = db.Column(db.String(120), unique=True, nullable=False)    # Email (must be unique)
    password_hash = db.Column(db.String(200), nullable=False)         # Encrypted password
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'admin' or 'customer'
    phone = db.Column(db.String(20), nullable=True)                   # Phone number (optional)
    is_verified = db.Column(db.Boolean, default=False)                # Email/phone verified
    verification_code = db.Column(db.String(6), nullable=True)        # 6-digit verification code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)      # When user joined
    
    def to_dict(self):
        """Convert user data to a dictionary (for JSON responses)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    """Table to store poultry products (eggs, chickens, feeds)"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)           # Product name
    category = db.Column(db.String(50), nullable=False)        # 'eggs', 'chickens', 'feeds'
    price = db.Column(db.Float, nullable=False)                # Price per unit
    stock_quantity = db.Column(db.Integer, nullable=False)     # How many in stock
    description = db.Column(db.Text, nullable=True)            # Product description
    image_url = db.Column(db.String(200), nullable=True)       # Product image (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'description': self.description,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Order(db.Model):
    """Table to store customer orders"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Who placed the order
    total_amount = db.Column(db.Float, nullable=False)        # Total price of order
    status = db.Column(db.String(20), default='pending')      # pending, confirmed, shipped, delivered
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship - connects order to customer
    customer = db.relationship('User', backref='orders')
    # Relationship - connects order to order items
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.username if self.customer else 'Unknown',
            'total_amount': self.total_amount,
            'status': self.status,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'items': [item.to_dict() for item in self.items],
            'payment': self.payment[0].to_dict() if self.payment else None
        }


class OrderItem(db.Model):
    """Table to store individual items within an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)           # How many of this product
    unit_price = db.Column(db.Float, nullable=False)           # Price at time of order
    
    # Relationship to get product details
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.quantity * self.unit_price
        }


class Payment(db.Model):
    """Table to store payment information"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='simulated')  # cash, card, simulated
    payment_status = db.Column(db.String(20), default='pending')    # pending, completed, failed
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order', backref='payment')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None
        }


class Advertisement(db.Model):
    """Table to store admin announcements/advertisements"""
    __tablename__ = 'advertisements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)          # Ad title
    content = db.Column(db.Text, nullable=False)               # Ad content/body
    image_url = db.Column(db.String(200), nullable=True)       # Optional image
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Admin who posted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    poster = db.relationship('User', backref='ads')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'posted_by': self.posted_by,
            'poster_name': self.poster.username if self.poster else 'Admin',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Cart(db.Model):
    """Table to store items in a customer's shopping cart"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'price': self.product.price if self.product else 0,
            'quantity': self.quantity,
            'subtotal': (self.product.price * self.quantity) if self.product else 0
        }