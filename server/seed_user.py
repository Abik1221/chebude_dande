import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.config import settings
from app.services.auth_service import auth_service

def seed_admin_user():
    # Create database engine
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "admin@example.com").first()
        
        if not existing_user:
            # Generate a default password
            default_password = "admin123"
            hashed_password = auth_service.get_password_hash(default_password)
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                full_name="System Admin",
                is_admin=True,
                credits=1000
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"✓ Admin user created successfully!")
            print(f"  Username: admin")
            print(f"  Password: admin123")
            print(f"  Email: admin@example.com")
        else:
            print(f"✓ Admin user already exists: {existing_user.username}")
    
    except Exception as e:
        print(f"✗ Error seeding admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()