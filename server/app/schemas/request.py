from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    TEXT_PROCESSING = "TEXT_PROCESSING"
    TTS_GENERATION = "TTS_GENERATION"
    AUDIO_PROCESSING = "AUDIO_PROCESSING"
    VIDEO_MERGING = "VIDEO_MERGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VideoGenerationRequest(BaseModel):
    description_text: str = Field(..., max_length=5000, description="Property description text")
    target_language: str = Field(..., pattern=r"^[a-z]{2}$", description="Target language code (e.g., 'en', 'te')")


class JobResponse(BaseModel):
    id: int
    status: JobStatus
    progress: int = 0
    input_file_path: Optional[str] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    id: int
    status: JobStatus
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    filename: str
    size: int
    path: str