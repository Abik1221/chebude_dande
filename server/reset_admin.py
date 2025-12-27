from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.config import settings
from app.services.auth_service import auth_service

def reset_admin():
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print(f"Resetting password for: {user.username}")
            user.hashed_password = auth_service.get_password_hash("admin123")
            db.commit()
            print("✓ Password reset to 'admin123'")
        else:
            print("Admin user not found. Creating new admin user...")
            hashed_password = auth_service.get_password_hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@metronavix.com",
                hashed_password=hashed_password,
                full_name="System Admin",
                is_admin=True,
                credits=1000
            )
            db.add(admin_user)
            db.commit()
            print("✓ Admin user created with password 'admin123'")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
