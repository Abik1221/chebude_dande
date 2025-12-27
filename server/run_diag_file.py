import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up logging to a file
with open("diag_output.txt", "w") as f:
    f.write("Starting Diagnostics...\n")
    try:
        from app.config import settings
        from app.database import Base, engine
        from app.models.user import User
        from app.services.auth_service import auth_service
        
        f.write(f"Database URL: {settings.database_url}\n")
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        users = db.query(User).all()
        f.write(f"Found {len(users)} users.\n")
        for u in users:
            f.write(f"User: {u.username}, Admin: {u.is_admin}\n")
            
        # Try to seed if missing
        if not any(u.username == "admin" for u in users):
            f.write("Admin missing. Seeding...\n")
            hashed = auth_service.get_password_hash("admin123")
            admin = User(
                username="admin",
                email="admin@metronavix-internal.com",
                hashed_password=hashed,
                is_admin=True,
                credits=1000
            )
            db.add(admin)
            db.commit()
            f.write("Admin seeded successfully.\n")
        else:
            f.write("Admin already exists. Resetting password...\n")
            admin = db.query(User).filter(User.username == "admin").first()
            admin.hashed_password = auth_service.get_password_hash("admin123")
            db.commit()
            f.write("Admin password reset to 'admin123'.\n")
            
    except Exception as e:
        f.write(f"Error: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())
