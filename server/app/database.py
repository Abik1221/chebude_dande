from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database URL
if settings.database_url.startswith("sqlite"):
    # For SQLite, use relative path
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    # For PostgreSQL/MySQL, use the provided URL
    SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Add connect_args for SQLite to allow multiple threads
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.job import Job, Language, Setting
from app.models.user import User, UserSession
from app.models.system import SystemLog

# Create all tables
def create_all_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()