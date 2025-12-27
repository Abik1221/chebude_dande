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
        existing_user = db.query(User).filter(User.username == "admin").first()
        
        default_password = "admin123"
        hashed_password = auth_service.get_password_hash(default_password)
        
        if not existing_user:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@metronavix-internal.com",
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
            print(f"  Password: {default_password}")
        else:
            print(f"✓ Admin user exists. Resetting password to default...")
            existing_user.hashed_password = hashed_password
            db.commit()
            print(f"✓ Password reset for 'admin' to: {default_password}")
    
    except Exception as e:
        print(f"✗ Error seeding/resetting admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()