from fastapi import HTTPException, status
from typing import Any, Dict
from loguru import logger
import traceback
from enum import Enum


class VideoGenerationError(Exception):
    """Base exception for video generation errors"""
    pass


class VideoGenerationErrorCode(str, Enum):
    """Error codes for video generation service"""
    INVALID_INPUT = "INVALID_INPUT"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    TTS_ERROR = "TTS_ERROR"
    VIDEO_PROCESSING_ERROR = "VIDEO_PROCESSING_ERROR"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


class VideoGenerationException(HTTPException):
    """Custom exception for video generation with structured error details"""
    
    def __init__(
        self,
        status_code: int,
        error_code: VideoGenerationErrorCode,
        detail: str,
        headers: Dict[str, Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.detail = detail
        self.status_code = status_code


def handle_video_generation_exception(
    exc: Exception,
    error_code: VideoGenerationErrorCode,
    log_error: bool = True
) -> VideoGenerationException:
    """
    Handle video generation exceptions and return appropriate HTTP exception
    """
    if log_error:
        logger.error(f"Video generation error: {str(exc)}")
        logger.error(traceback.format_exc())
    
    # Map specific exception types to appropriate HTTP status codes
    if isinstance(exc, VideoGenerationException):
        return exc
    elif isinstance(exc, ValueError):
        return VideoGenerationException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=VideoGenerationErrorCode.INVALID_INPUT,
            detail=str(exc)
        )
    elif isinstance(exc, FileNotFoundError):
        return VideoGenerationException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=VideoGenerationErrorCode.FILE_NOT_FOUND,
            detail=str(exc)
        )
    else:
        return VideoGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            detail=f"An error occurred: {str(exc)}"
        )


def setup_logging():
    """
    Set up logging configuration
    """
    # Remove default logger configuration
    logger.remove()
    
    # Add custom logger configuration
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        serialize=False
    )
    
    # Also log to console in development
    logger.add(
        lambda msg: print(msg),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        colorize=True
    )
    
    logger.info("Logging setup complete")