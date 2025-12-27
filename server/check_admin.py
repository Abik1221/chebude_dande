from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.config import settings
import bcrypt

def check_admin():
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print(f"User: {user.username}")
            print(f"Hash: {user.hashed_password}")
            
            # Test direct bcrypt verification
            try:
                is_valid = bcrypt.checkpw("admin123".encode('utf-8'), user.hashed_password.encode('utf-8'))
                print(f"Verify 'admin123': {is_valid}")
            except Exception as e:
                print(f"Error verifying: {e}")
        else:
            print("Admin user not found.")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
