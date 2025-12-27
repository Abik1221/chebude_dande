import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path to include current dir
sys.path.append(os.getcwd())

with open("login_debug.txt", "w") as f:
    f.write("Starting Login Debug...\n")
    try:
        from app.database import SessionLocal
        from app.services.auth_service import auth_service
        from app.models.user import User
        
        db = SessionLocal()
        username = "admin"
        password = "admin123"
        
        f.write(f"Attempting login for: {username}\n")
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            f.write("ERROR: User 'admin' not found in database!\n")
        else:
            f.write(f"User found: {user.username}\n")
            f.write(f"Hash in DB: {user.hashed_password}\n")
            
            # Manual check with AuthService verify_password
            res = auth_service.verify_password(password, user.hashed_password)
            f.write(f"auth_service.verify_password result: {res}\n")
            
            # Manual check using auth_service.authenticate_user (which the API uses)
            auth_user = auth_service.authenticate_user(db, username, password)
            f.write(f"auth_service.authenticate_user result: {auth_user is not None}\n")
            
            if not res:
                # Try to re-hash and see if it match
                new_hash = auth_service.get_password_hash(password)
                f.write(f"New hash for 'admin123': {new_hash}\n")
                f.write(f"Verification against new hash: {auth_service.verify_password(password, new_hash)}\n")

        db.close()
    except Exception as e:
        f.write(f"Unexpected error: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())
