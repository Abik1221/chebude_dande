#!/usr/bin/env python3
"""
Migration script to update existing user passwords from SHA256 to bcrypt hashing.
This should be run once after updating the auth system.
"""

import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.config import settings
from app.services.auth_service import auth_service

def migrate_user_passwords():
    """Migrate existing user passwords from SHA256 to bcrypt"""
    # Create database engine
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        
        if not users:
            print("No users found in database.")
            return
        
        print(f"Found {len(users)} users to migrate...")
        
        # For existing users, we need to reset their passwords since we can't reverse SHA256
        # We'll set a default password that they'll need to change
        default_password = "TempPass123"
        
        migrated_count = 0
        for user in users:
            # Check if password is already bcrypt (bcrypt hashes start with $2b$)
            if user.hashed_password.startswith('$2b$'):
                print(f"User {user.username} already has bcrypt password, skipping...")
                continue
            
            # Update to bcrypt hash (ensure password is within bcrypt's 72 byte limit)
            password_to_hash = default_password[:72]  # Truncate if necessary
            user.hashed_password = auth_service.get_password_hash(password_to_hash)
            migrated_count += 1
            
            print(f"Migrated user: {user.username}")
        
        if migrated_count > 0:
            db.commit()
            print(f"\n✓ Successfully migrated {migrated_count} users!")
            print(f"⚠️  All migrated users now have the temporary password: {default_password}")
            print("⚠️  Users should change their passwords after logging in.")
        else:
            print("No users needed migration.")
    
    except Exception as e:
        print(f"✗ Error migrating passwords: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_passwords()