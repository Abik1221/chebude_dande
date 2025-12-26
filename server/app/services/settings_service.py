from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.job import Setting
from app.config import settings
import json


class SettingsService:
    """
    Service for managing application settings
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_setting(self, key: str) -> Optional[Setting]:
        """
        Get a setting by key
        """
        return self.db.query(Setting).filter(Setting.key == key).first()
    
    def get_setting_value(self, key: str, default: Any = None) -> Any:
        """
        Get the value of a setting
        """
        setting = self.get_setting(key)
        if not setting:
            return default
        
        # Convert the value based on the setting type
        if setting.type == "integer":
            return int(setting.value)
        elif setting.type == "boolean":
            return setting.value.lower() in ("true", "1", "yes", "on")
        elif setting.type == "json":
            try:
                return json.loads(setting.value)
            except json.JSONDecodeError:
                return default
        else:
            return setting.value
    
    def set_setting(self, key: str, value: Any, description: str = None, type: str = "string") -> Setting:
        """
        Set a setting value
        """
        # Convert value to string based on type
        if type == "json":
            value = json.dumps(value)
        else:
            value = str(value)
        
        setting = self.get_setting(key)
        if setting:
            # Update existing setting
            setting.value = value
            setting.description = description
            setting.type = type
        else:
            # Create new setting
            setting = Setting(
                key=key,
                value=value,
                description=description,
                type=type
            )
            self.db.add(setting)
        
        self.db.commit()
        self.db.refresh(setting)
        return setting
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary
        """
        settings = self.db.query(Setting).all()
        result = {}
        for setting in settings:
            result[setting.key] = self.get_setting_value(setting.key)
        return result
    
    def update_multiple_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update multiple settings at once
        """
        results = {}
        for key, value in settings_dict.items():
            # Try to determine the type automatically or use a mapping
            setting_type = self._infer_type(value)
            result = self.set_setting(key, value, type=setting_type)
            results[key] = result.value
        return results
    
    def _infer_type(self, value: Any) -> str:
        """
        Infer the type of a setting value
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, (dict, list)):
            return "json"
        else:
            return "string"


# Global settings service instance (in production, you'd want to use dependency injection)
def get_settings_service(db: Session) -> SettingsService:
    """
    Get settings service instance with database session
    """
    return SettingsService(db)