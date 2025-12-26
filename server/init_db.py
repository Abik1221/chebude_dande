from sqlalchemy.orm import sessionmaker
from app.database import engine, Base
from app.models.job import Language

# Create tables
Base.metadata.create_all(bind=engine)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Add default languages if they don't exist
default_languages = [
    {"code": "en", "name": "English", "tts_voice": "nova"},
    {"code": "te", "name": "Telugu", "tts_voice": "onyx"},
]

for lang_data in default_languages:
    existing_lang = db.query(Language).filter(Language.code == lang_data["code"]).first()
    if not existing_lang:
        language = Language(**lang_data)
        db.add(language)

db.commit()
db.close()

print("Database initialized with default languages")