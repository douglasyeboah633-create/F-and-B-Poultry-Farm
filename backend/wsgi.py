"""
WSGI entry point for gunicorn - Initializes database on startup
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app, db, bcrypt
from backend.models import User

# Initialize database tables on startup
with app.app_context():
    try:
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
    except Exception as e:
        print(f"[WARNING] Database setup issue: {e}")

# Export app for gunicorn
application = app