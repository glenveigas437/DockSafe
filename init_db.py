#!/usr/bin/env python3
"""
Initialize the DockSafe database and create default user
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
import bcrypt

def init_database():
    """Initialize database and create default user"""
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if any users exist
        user_count = User.query.count()
        
        if user_count == 0:
            print("📝 No users found in database.")
            print("   Users will be created automatically when they sign in with Google.")
            print("   Make sure to configure Google OAuth credentials in your .env file.")
        else:
            print(f"📊 Total users in database: {user_count}")
        
        print("🎉 Database initialization completed!")
        print("\n📋 Next steps:")
        print("   1. Configure Google OAuth credentials (see GOOGLE_OAUTH_SETUP.md)")
        print("   2. Set up your .env file with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        print("   3. Run: python3 run.py")
        print("   4. Visit: http://localhost:5000/auth/login")

if __name__ == '__main__':
    init_database()
