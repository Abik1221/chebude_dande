import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.user import User
from app.services.auth_service import auth_service

def verify_admin():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("User 'admin' not found!")
            return
            
        print(f"User: {user.username}")
        print(f"Hashed Password in DB: {user.hashed_password}")
        
        password_to_test = "admin123"
        
        # Test 1: Direct bcrypt check
        try:
            matched_direct = bcrypt.checkpw(password_to_test.encode('utf-8'), user.hashed_password.encode('utf-8'))
            print(f"Direct bcrypt match: {matched_direct}")
        except Exception as e:
            print(f"Direct bcrypt error: {e}")
            
        # Test 2: AuthService check
        matched_service = auth_service.verify_password(password_to_test, user.hashed_password)
        print(f"AuthService match: {matched_service}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_admin()
