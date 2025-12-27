from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.config import settings

def list_users():
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        print(f"Total users found: {len(users)}")
        for user in users:
            print(f"ID: {user.id} | Username: {user.username} | Email: {user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
