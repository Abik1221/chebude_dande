from alembic.config import Config
from alembic import command
import os

def run_migrations():
    # Change to the directory containing alembic.ini
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Run the upgrade
    try:
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {str(e)}")

if __name__ == "__main__":
    run_migrations()