from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.settings_service import SettingsService, get_settings_service
from app.models.job import Setting

router = APIRouter()


@router.get("/settings", summary="Get all settings")
async def get_all_settings(
    settings_service: SettingsService = Depends(get_settings_service),
    db: Session = Depends(get_db)
):
    """
    Retrieve all application settings
    """
    try:
        settings = settings_service.get_all_settings()
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/{key}", summary="Get specific setting")
async def get_setting(
    key: str,
    settings_service: SettingsService = Depends(get_settings_service),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific setting by key
    """
    try:
        setting = settings_service.get_setting_value(key)
        if setting is None:
            raise HTTPException(status_code=404, detail="Setting not found")
        
        return {"key": key, "value": setting}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{key}", summary="Update specific setting")
async def update_setting(
    key: str,
    value: str,
    description: str = None,
    type: str = "string",
    settings_service: SettingsService = Depends(get_settings_service),
    db: Session = Depends(get_db)
):
    """
    Update a specific setting
    """
    try:
        # Validate type parameter
        valid_types = ["string", "integer", "boolean", "json"]
        if type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")
        
        # If type is json, validate the JSON format
        if type == "json":
            import json as json_lib
            try:
                json_lib.loads(value)
            except json_lib.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        updated_setting = settings_service.set_setting(key, value, description, type)
        return {"key": updated_setting.key, "value": updated_setting.value, "type": updated_setting.type}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", summary="Update multiple settings")
async def update_multiple_settings(
    settings: Dict[str, Any],
    settings_service: SettingsService = Depends(get_settings_service),
    db: Session = Depends(get_db)
):
    """
    Update multiple settings at once
    """
    try:
        # The settings dict should have the format: {key: value}
        # We'll infer types automatically
        updated_settings = settings_service.update_multiple_settings(settings)
        return {"updated_settings": updated_settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/initialize", summary="Initialize default settings")
async def initialize_default_settings(
    settings_service: SettingsService = Depends(get_settings_service),
    db: Session = Depends(get_db)
):
    """
    Initialize default settings for the application
    """
    try:
        default_settings = {
            "app_name": {"value": "EstateVision AI", "description": "Name of the application", "type": "string"},
            "app_version": {"value": "1.0.0", "description": "Version of the application", "type": "string"},
            "default_language": {"value": "en", "description": "Default language for video generation", "type": "string"},
            "max_video_size_mb": {"value": "100", "description": "Maximum allowed video size in MB", "type": "integer"},
            "max_description_length": {"value": "5000", "description": "Maximum length of property description", "type": "integer"},
            "enable_tts_fallback": {"value": "true", "description": "Enable fallback TTS service", "type": "boolean"},
            "tts_fallback_service": {"value": "google", "description": "Fallback TTS service to use", "type": "string"},
            "video_processing_quality": {"value": "720p", "description": "Default video processing quality", "type": "string"},
            "enable_email_notifications": {"value": "false", "description": "Enable email notifications for job completion", "type": "boolean"},
            "email_smtp_server": {"value": "smtp.gmail.com", "description": "SMTP server for email notifications", "type": "string"},
            "email_smtp_port": {"value": "587", "description": "SMTP port for email notifications", "type": "integer"},
            "enable_api_rate_limiting": {"value": "true", "description": "Enable API rate limiting", "type": "boolean"},
            "api_rate_limit_requests": {"value": "100", "description": "Number of requests allowed per window", "type": "integer"},
            "api_rate_limit_window": {"value": "3600", "description": "Time window for rate limiting in seconds", "type": "integer"},
            "default_tts_voice": {"value": "nova", "description": "Default TTS voice to use", "type": "string"},
            "tts_speed": {"value": "1.0", "description": "Default TTS speech speed", "type": "string"},
            "enable_background_processing": {"value": "true", "description": "Enable background job processing", "type": "boolean"},
            "max_concurrent_jobs": {"value": "5", "description": "Maximum number of concurrent video generation jobs", "type": "integer"},
        }
        
        for key, setting_info in default_settings.items():
            settings_service.set_setting(
                key, 
                setting_info["value"], 
                setting_info["description"], 
                setting_info["type"]
            )
        
        return {"message": "Default settings initialized successfully", "count": len(default_settings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))