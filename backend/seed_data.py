"""
SEED DATA SCRIPT for F and B Poultry Farm Limited
================================================
Run this script to add sample products to the database.
This helps you test the system with some data.

How to run: python seed_data.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import app, bcrypt
from models import db, User, Product, Advertisement

def seed():
    """Add sample data to the database"""
    
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Check if we already have products (don't duplicate)
        if Product.query.count() > 0:
            print("[WARNING] Database already has products. Skipping seed.")
            return
        
        print("[INFO] Seeding database with sample data...")
        
        # ----- SAMPLE PRODUCTS -----
        products = [
            # Eggs
            Product(
                name="Crate of Fresh Eggs (30 pcs)",
                category="eggs",
                price=3500.00,
                stock_quantity=50,
                description="Farm-fresh eggs straight from our healthy layers. 30 eggs per crate.",
                image_url=""
            ),
            Product(
                name="Tray of Eggs (12 pcs)",
                category="eggs",
                price=1500.00,
                stock_quantity=100,
                description="A dozen fresh eggs perfect for your family.",
                image_url=""
            ),
            Product(
                name="Half Crate of Eggs (15 pcs)",
                category="eggs",
                price=2000.00,
                stock_quantity=75,
                description="Half crate of fresh eggs - just the right amount.",
                image_url=""
            ),
            
            # Chickens
            Product(
                name="Broiler Chicken (Live)",
                category="chickens",
                price=4500.00,
                stock_quantity=30,
                description="Healthy broiler chicken ready for sale. Weight: 2-3kg.",
                image_url=""
            ),
            Product(
                name="Layers Chicken (Live)",
                category="chickens",
                price=5000.00,
                stock_quantity=25,
                description="Mature laying hen ready for egg production.",
                image_url=""
            ),
            Product(
                name="Day-Old Chicks (Broiler)",
                category="chickens",
                price=800.00,
                stock_quantity=200,
                description="Just hatched broiler chicks. Vaccinated and healthy.",
                image_url=""
            ),
            
            # Feeds
            Product(
                name="Broiler Starter Feed (50kg)",
                category="feeds",
                price=12500.00,
                stock_quantity=20,
                description="High-quality starter feed for broiler chicks (0-4 weeks).",
                image_url=""
            ),
            Product(
                name="Layers Feed (50kg)",
                category="feeds",
                price=11000.00,
                stock_quantity=15,
                description="Complete feed for laying hens. Produces strong eggshells.",
                image_url=""
            ),
            Product(
                name="Growers Feed (50kg)",
                category="feeds",
                price=9500.00,
                stock_quantity=18,
                description="Feed for growing chickens (5-16 weeks).",
                image_url=""
            ),
            Product(
                name="Chick Mash (25kg)",
                category="feeds",
                price=6500.00,
                stock_quantity=25,
                description="Fine mash for day-old chicks. Easy to digest.",
                image_url=""
            ),
        ]
        
        for product in products:
            db.session.add(product)
        
        # ----- SAMPLE ANNOUNCEMENT -----
        announcement = Advertisement(
            title="[WELCOME] F and B Poultry Farm is Live!",
            content="We are excited to launch our online store! Browse our products for fresh eggs, healthy chickens, and quality feeds. Enjoy farm-fresh products delivered to your doorstep.",
            posted_by=1  # Admin user (ID=1)
        )
        db.session.add(announcement)
        
        db.session.commit()
        
        print(f"[OK] Added {len(products)} products")
        print("[OK] Added welcome announcement")
        print("")
        print("[SUMMARY] Sample Data:")
        print("   - Fresh Eggs: 3 products")
        print("   - Chickens: 3 products")
        print("   - Feeds: 4 products")
        print("   - Announcements: 1")
        print("")
        print("[DONE] Database seeded successfully!")
        print("")
        print("You can now start the server and login:")
        print("   Admin: admin@fandb.com / admin123")

if __name__ == '__main__':
    seed()