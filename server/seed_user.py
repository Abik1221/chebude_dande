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
        existing_user = db.query(User).filter(User.email == "nahi@gmail.com").first()
        
        if not existing_user:
            # Generate a default password if not specified
            default_password = "123abcdsystem"
            hashed_password = auth_service.get_password_hash(default_password)
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="nahi@gmail.com",
                hashed_password=hashed_password,
                full_name="System Admin",
                is_admin=True,
                credits=1000  # Give admin plenty of credits
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"Admin user created successfully!")
            print(f"Email: nahi@gmail.com")
            print(f"Password: 123abcdsystem")
            print(f"Username: admin")
            print(f"User ID: {admin_user.id}")
        else:
            print(f"Admin user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Username: {existing_user.username}")
            print(f"User ID: {existing_user.id}")
    
    except Exception as e:
        print(f"Error seeding admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()