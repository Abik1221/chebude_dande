from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "Property Video Generator API"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = f"sqlite:///./property_video_generator.db"
    database_pool_size: int = 20
    database_pool_overflow: int = 0
    
    # OpenAI settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "nova"
    
    # Google Cloud TTS settings
    google_cloud_credentials_path: Optional[str] = os.getenv("GOOGLE_CLOUD_CREDENTIALS_PATH")
    
    # File storage settings
    upload_folder: str = "uploads"
    output_folder: str = "outputs"
    temp_folder: str = "temp"
    
    # Processing settings
    max_video_size_mb: int = 100  # 100MB max
    allowed_video_formats: list = ["mp4", "mov", "avi", "mkv", "wmv"]
    max_description_length: int = 5000  # characters
    
    # Job processing settings
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"


settings = Settings()