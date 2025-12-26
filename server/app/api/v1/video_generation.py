from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import subprocess
from datetime import datetime

from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.request import VideoGenerationRequest, JobResponse, JobStatusResponse, UploadResponse
from app.workflows.video_generation import VideoGenerationWorkflow
from app.config import settings
from app.services.video_service import VideoProcessingService
from app.services.job_service import JobTracker
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from loguru import logger
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add("video_generation.log", rotation="10 MB")

router = APIRouter()
security = HTTPBearer()


def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to destination path"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as buffer:
        buffer.write(upload_file.file.read())
    return destination


@router.post("/generate")
async def generate_video(
    description_text: str = Form(...),
    target_language: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a video generation job
    """
    logger.info(f"Received video generation request from user {current_user.username}")
    
    # Basic validation
    if len(description_text) > settings.max_description_length:
        raise HTTPException(
            status_code=400,
            detail=f"Description text too long. Maximum length: {settings.max_description_length} characters"
        )
    
    # Validate file is provided
    if not video_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_folder, exist_ok=True)
    
    # Save the uploaded video file
    unique_filename = f"{uuid.uuid4()}_{video_file.filename}"
    video_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        save_upload_file(video_file, video_path)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error saving uploaded file")
    
    # Create a job in the database
    try:
        job = Job(
            status="PENDING",
            progress=0,
            input_file_path=video_path,
            description_text=description_text,
            target_language=target_language
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job.id} for video generation")
        
        # Start the video processing in the background
        import asyncio
        asyncio.create_task(process_video_with_narration(job.id, video_path, description_text, target_language))
        
        return {
            "id": job.id,
            "status": job.status,
            "progress": job.progress
        }
        
    except Exception as e:
        # Clean up the saved file if DB operation fails
        if os.path.exists(video_path):
            os.remove(video_path)
        logger.error(f"Error creating job in database: {e}")
        raise HTTPException(status_code=500, detail="Error creating video generation job")


async def process_video_with_narration(job_id: int, video_path: str, description_text: str, target_language: str):
    """
    Process video with AI narration in the background
    """
    from app.database import get_db
    from app.services.simple_tts import TTSManager
    import tempfile
    import subprocess
    
    db = next(get_db())
    
    try:
        # Update job status to processing
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
            
        job.status = "PROCESSING"
        job.progress = 10
        db.commit()
        
        logger.info(f"Starting video processing for job {job_id}")
        
        # Step 1: Generate audio narration using simple TTS
        job.status = "GENERATING_AUDIO"
        job.progress = 30
        db.commit()
        
        logger.info(f"Starting TTS generation for job {job_id}")
        logger.info(f"Description text: {description_text[:100]}...")
        logger.info(f"Target language: {target_language}")
        
        tts_manager = TTSManager()
        
        # Generate audio content
        audio_content = tts_manager.synthesize_speech(
            description_text,
            target_language,
            "default"
        )
        
        logger.info(f"Generated audio content size: {len(audio_content)} bytes")
        
        # Save audio to permanent file for debugging
        audio_filename = f"narration_{uuid.uuid4()}.wav"
        audio_path = os.path.join(settings.upload_folder, audio_filename)
        
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(audio_content)
        
        logger.info(f"Generated audio narration saved to: {audio_path}")
        
        # Get audio duration for logging
        audio_duration_cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_path
        ]
        audio_duration_result = subprocess.run(audio_duration_cmd, capture_output=True, text=True)
        if audio_duration_result.returncode == 0:
            audio_duration = float(audio_duration_result.stdout.strip())
            logger.info(f"Generated audio duration: {audio_duration} seconds")
        else:
            logger.warning("Could not determine audio duration")
        
        # Step 2: Get video duration first
        job.status = "ANALYZING_VIDEO"
        job.progress = 50
        db.commit()
        
        # Get video duration using ffprobe
        duration_cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        
        if duration_result.returncode != 0:
            raise Exception(f"Failed to get video duration: {duration_result.stderr}")
        
        video_duration = float(duration_result.stdout.strip())
        logger.info(f"Video duration: {video_duration} seconds")
        
        # Step 3: Merge audio with video using ffmpeg
        job.status = "MERGING_VIDEO"
        job.progress = 70
        db.commit()
        
        # Create output filename
        output_filename = f"output_{uuid.uuid4()}.mp4"
        output_path = os.path.join(settings.upload_folder, output_filename)
        
        # Use ffmpeg to stretch/compress narration to match video duration and mix with original audio
        ffmpeg_cmd = [
            'ffmpeg', '-y',  # -y to overwrite output file
            '-i', video_path,  # Input video
            '-i', audio_path,  # Input audio (narration)
            '-filter_complex', 
            f'[1:a]apad=whole_dur={video_duration}[narration];[0:a][narration]amix=inputs=2:duration=first:dropout_transition=3[aout]',
            '-map', '0:v',     # Map video from first input
            '-map', '[aout]',  # Map mixed audio
            '-c:v', 'copy',    # Copy video stream (no re-encoding)
            '-c:a', 'aac',     # Encode audio as AAC
            '-b:a', '128k',    # Audio bitrate
            '-t', str(video_duration),  # Ensure output matches video duration
            output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Success
            job.status = "COMPLETED"
            job.progress = 100
            job.output_file_path = output_path
            logger.info(f"Successfully completed video processing for job {job_id}")
        else:
            # Error
            job.status = "FAILED"
            job.error_message = f"FFmpeg error: {result.stderr}"
            logger.error(f"FFmpeg failed for job {job_id}: {result.stderr}")
        
        # Don't clean up audio file for debugging
        # if os.path.exists(audio_path):
        #     os.remove(audio_path)
        logger.info(f"Audio file kept for debugging: {audio_path}")
            
    except Exception as e:
        logger.error(f"Error processing video for job {job_id}: {str(e)}")
        job.status = "FAILED"
        job.error_message = str(e)
        
    finally:
        db.commit()
        db.close()


async def run_video_generation_workflow(input_data: dict, job_id: int):
    """
    Run the video generation workflow and update job status
    """
    db = next(get_db())
    workflow = VideoGenerationWorkflow()
    
    try:
        # Update job status to PROCESSING
        job_tracker = JobTracker(db)
        job_tracker.update_job_status(
            job_id=job_id,
            status="PROCESSING",
            progress=5
        )
        
        # Run the workflow
        result = await workflow.run_workflow(input_data)
        
        # Update job with results
        job_tracker.update_job_status(
            job_id=job_id,
            status=result.status,
            progress=result.progress,
            output_file_path=result.output_path,
            error_message=result.error_message
        )
        
        logger.info(f"Job {job_id} completed with status: {result.status}")
    
    except Exception as e:
        logger.error(f"Error running video generation workflow for job {job_id}: {e}")
        # Update job status to FAILED
        job_tracker = JobTracker(db)
        job_tracker.update_job_status(
            job_id=job_id,
            status="FAILED",
            progress=100,
            error_message=str(e)
        )
    
    finally:
        db.close()


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a video generation job
    """
    job_tracker = JobTracker(db)
    job = job_tracker.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_video(video_file: UploadFile = File(...)):
    """
    Upload a video file without starting generation
    """
    # Validate file type
    if not video_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    file_extension = video_file.filename.split(".")[-1].lower()
    if file_extension not in settings.allowed_video_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed formats: {', '.join(settings.allowed_video_formats)}"
        )
    
    # Validate file size
    video_file.file.seek(0, 2)  # Seek to end of file
    file_size = video_file.file.tell()
    video_file.file.seek(0)  # Seek back to beginning
    
    max_size_bytes = settings.max_video_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_video_size_mb}MB"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_folder, exist_ok=True)
    
    # Save the uploaded video file
    unique_filename = f"{uuid.uuid4()}_{video_file.filename}"
    video_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        save_upload_file(video_file, video_path)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error saving uploaded file")
    
    return UploadResponse(
        filename=unique_filename,
        size=file_size,
        path=video_path
    )


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    # In a real implementation, this would come from the database
    return [
        {"code": "en", "name": "English", "tts_voice": "nova"},
        {"code": "te", "name": "Telugu", "tts_voice": "onyx"}
    ]


@router.get("/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """
    List video generation jobs with optional filtering
    """
    job_tracker = JobTracker(db)
    jobs = job_tracker.list_jobs(
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [
        JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        ) for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete a video generation job
    """
    job_tracker = JobTracker(db)
    success = job_tracker.delete_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.post("/generate-simple")
async def generate_video_simple(
    description_text: str = Form(...),
    target_language: str = Form(...),
    video_file: UploadFile = File(...)
):
    """
    Simple test endpoint for video generation
    """
@router.post("/generate-auth-test")
async def generate_video_auth_test(
    description_text: str = Form(...),
    target_language: str = Form(...),
    video_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint with authentication
    """
@router.post("/generate-db-test")
async def generate_video_db_test(
    description_text: str = Form(...),
    target_language: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint with database and authentication
    """
    return {
        "message": "Success with auth and db",
        "description_text": description_text,
        "target_language": target_language,
        "filename": video_file.filename,
        "user": current_user.username
    }