from sqlalchemy.orm import sessionmaker
from app.database import engine, Base, create_all_tables
from app.models.job import Language, Setting
from app.models.user import User
from app.config import settings
import os

print("Initializing SQLite database...")
print(f"Database URL: {settings.database_url}")

# Create all tables
create_all_tables()
print("✓ Database tables created")

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Add default languages if they don't exist
    default_languages = [
        {"code": "en", "name": "English", "tts_voice": "nova"},
        {"code": "te", "name": "Telugu", "tts_voice": "onyx"},
        {"code": "es", "name": "Spanish", "tts_voice": "alloy"},
        {"code": "fr", "name": "French", "tts_voice": "echo"},
        {"code": "de", "name": "German", "tts_voice": "fable"},
    ]

    for lang_data in default_languages:
        existing_lang = db.query(Language).filter(Language.code == lang_data["code"]).first()
        if not existing_lang:
            language = Language(**lang_data)
            db.add(language)
            print(f"✓ Added language: {lang_data['name']} ({lang_data['code']})")

    # Add default settings if they don't exist
    default_settings = [
        {"key": "app_name", "value": "Metronavix", "description": "Application name", "type": "string"},
        {"key": "app_version", "value": "1.0.0", "description": "Application version", "type": "string"},
        {"key": "default_language", "value": "en", "description": "Default language for video generation", "type": "string"},
        {"key": "max_video_size_mb", "value": "100", "description": "Maximum video size in MB", "type": "integer"},
        {"key": "max_description_length", "value": "5000", "description": "Maximum description length", "type": "integer"},
        {"key": "enable_tts_fallback", "value": "true", "description": "Enable TTS fallback", "type": "boolean"},
        {"key": "default_tts_voice", "value": "nova", "description": "Default TTS voice", "type": "string"},
        {"key": "max_concurrent_jobs", "value": "5", "description": "Maximum concurrent jobs", "type": "integer"},
    ]

    for setting_data in default_settings:
        existing_setting = db.query(Setting).filter(Setting.key == setting_data["key"]).first()
        if not existing_setting:
            setting = Setting(**setting_data)
            db.add(setting)
            print(f"✓ Added setting: {setting_data['key']}")

    # Create default admin user if it doesn't exist
    from app.services.auth_service import auth_service
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        hashed_password = auth_service.get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@metronavix-internal.com",
            hashed_password=hashed_password,
            full_name="System Admin",
            is_admin=True,
            credits=1000
        )
        db.add(admin_user)
        print("✓ Created default admin user ('admin' / 'admin123')")

    db.commit()
    print("\n🎉 Database initialization completed successfully!")
    
    # Show database file location
    if settings.database_url.startswith("sqlite"):
        db_file = settings.database_url.replace("sqlite:///", "")
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            print(f"📁 Database file: {os.path.abspath(db_file)} ({file_size} bytes)")

except Exception as e:
    print(f"❌ Error during database initialization: {e}")
    db.rollback()
    raise
finally:
    db.close()