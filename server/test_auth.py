#!/usr/bin/env python3
"""
Test script to verify the authentication system works correctly
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.config import settings
from app.services.auth_service import auth_service

def test_auth_system():
    """Test the authentication system"""
    # Create database engine
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Testing authentication system...")
        
        # Test 1: Get existing admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print(f"✓ Found admin user: {admin_user.username}")
            
            # Test 2: Authenticate with correct password
            auth_result = auth_service.authenticate_user(db, "admin", "TempPass123")
            if auth_result:
                print("✓ Authentication with correct password: SUCCESS")
            else:
                print("✗ Authentication with correct password: FAILED")
            
            # Test 3: Authenticate with wrong password
            auth_result = auth_service.authenticate_user(db, "admin", "wrongpassword")
            if not auth_result:
                print("✓ Authentication with wrong password: CORRECTLY REJECTED")
            else:
                print("✗ Authentication with wrong password: INCORRECTLY ACCEPTED")
            
            # Test 4: Create JWT token
            token = auth_service.create_access_token(data={"sub": str(admin_user.id)})
            if token:
                print("✓ JWT token creation: SUCCESS")
                
                # Test 5: Verify JWT token
                payload = auth_service.verify_token(token)
                if payload and payload.get("sub") == str(admin_user.id):
                    print("✓ JWT token verification: SUCCESS")
                else:
                    print("✗ JWT token verification: FAILED")
            else:
                print("✗ JWT token creation: FAILED")
        else:
            print("✗ Admin user not found")
        
        print("\n" + "="*50)
        print("Authentication system test completed!")
        
    except Exception as e:
        print(f"✗ Error testing auth system: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_system()