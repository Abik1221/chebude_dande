import os
from sqlalchemy import create_engine, text
from app.database import Base
from app.config import settings

def create_database():
    # Ensure we're in the right directory
    os.chdir('/home/nahomkeneni/upwork_projects/chebude_dande/server')
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database URL: {settings.database_url}")
    
    # Create the database engine
    engine = create_engine(settings.database_url, connect_args={'check_same_thread': False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"Created tables: {tables}")
    
    print('Database and tables created successfully!')
    
    # Check if database file exists
    db_path = settings.database_url.replace('sqlite:///', '')
    print(f"Database file path: {db_path}")
    print(f"Database file exists: {os.path.exists(db_path)}")

if __name__ == "__main__":
    create_database()