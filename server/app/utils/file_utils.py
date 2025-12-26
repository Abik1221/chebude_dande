import os
import shutil
from pathlib import Path
from typing import Optional
from app.config import settings
from loguru import logger


def create_directory_if_not_exists(path: str) -> bool:
    """
    Create directory if it doesn't exist
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def validate_file_path(file_path: str) -> bool:
    """
    Validate if the file path is safe and within allowed directories
    """
    try:
        # Resolve the path to prevent directory traversal
        resolved_path = Path(file_path).resolve()
        
        # Check if the resolved path is within allowed directories
        allowed_paths = [
            Path(settings.upload_folder).resolve(),
            Path(settings.output_folder).resolve(),
            Path(settings.temp_folder).resolve()
        ]
        
        for allowed_path in allowed_paths:
            if resolved_path.is_relative_to(allowed_path):
                return True
        
        logger.warning(f"File path {file_path} is not in allowed directories")
        return False
    except Exception:
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return None


def safe_delete_file(file_path: str) -> bool:
    """
    Safely delete a file after validating the path
    """
    if not validate_file_path(file_path):
        logger.error(f"Unsafe file path for deletion: {file_path}")
        return False
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        else:
            logger.warning(f"File does not exist: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def cleanup_directory(directory: str, exclude_files: list = None) -> int:
    """
    Clean up files in a directory, excluding specified files
    """
    if exclude_files is None:
        exclude_files = []
    
    deleted_count = 0
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path) and filename not in exclude_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up directory {directory}: {e}")
    
    return deleted_count


def get_file_extension(file_path: str) -> str:
    """
    Get the file extension without the dot
    """
    return Path(file_path).suffix.lstrip('.').lower()


def validate_video_file(video_path: str) -> tuple[bool, str]:
    """
    Validate video file format and size
    Returns (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(video_path):
        return False, f"Video file does not exist: {video_path}"
    
    # Check file extension
    ext = get_file_extension(video_path)
    if ext not in settings.allowed_video_formats:
        return False, f"Unsupported video format: {ext}. Allowed formats: {settings.allowed_video_formats}"
    
    # Check file size
    file_size = get_file_size(video_path)
    if file_size is None:
        return False, f"Could not determine file size: {video_path}"
    
    max_size_bytes = settings.max_video_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large: {file_size} bytes. Maximum size: {settings.max_video_size_mb}MB"
    
    return True, ""