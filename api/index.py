"""
Vercel Serverless Function - Wraps Flask app for Vercel deployment
"""
import sys
import os

# Add parent directory to path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel expects the app to be exported as 'app'
app = app