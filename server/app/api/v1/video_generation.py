from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models.job import Job
from app.schemas.request import VideoGenerationRequest, JobResponse, JobStatusResponse, UploadResponse
from app.workflows.video_generation import VideoGenerationWorkflow
from app.config import settings
from app.services.video_service import VideoProcessingService
from app.services.job_service import JobTracker
from loguru import logger

router = APIRouter()


def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to destination path"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as buffer:
        buffer.write(upload_file.file.read())
    return destination


@router.post("/generate", response_model=JobResponse)
async def generate_video(
    video_file: UploadFile = File(...),
    description_text: str = Form(...),
    target_language: str = Form(...)
):
    """
    Submit a video generation job
    """
    # Validate inputs
    if len(description_text) > settings.max_description_length:
        raise HTTPException(
            status_code=400,
            detail=f"Description text too long. Maximum length: {settings.max_description_length} characters"
        )
    
    # Validate file type
    file_extension = video_file.filename.split(".")[-1].lower()
    if file_extension not in settings.allowed_video_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed formats: {settings.allowed_video_formats}"
        )
    
    # Validate file size
    # Note: FastAPI doesn't provide file size directly, so we'll check after saving
    video_file.file.seek(0, 2)  # Seek to end of file
    file_size = video_file.file.tell()
    video_file.file.seek(0)  # Seek back to beginning
    
    max_size_bytes = settings.max_video_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_video_size_mb}MB"
        )
    
    # Save the uploaded video file
    unique_filename = f"{uuid.uuid4()}_{video_file.filename}"
    video_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        save_upload_file(video_file, video_path)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error saving uploaded file")
    
    # Create a new job in the database
    db = next(get_db())
    try:
        job_tracker = JobTracker(db)
        job = job_tracker.create_job(
            input_file_path=video_path,
            description_text=description_text,
            target_language=target_language
        )
        
        job_id = job.id
    except Exception as e:
        db.close()
        # Clean up the saved file if DB operation fails
        if os.path.exists(video_path):
            os.remove(video_path)
        logger.error(f"Error creating job in database: {e}")
        raise HTTPException(status_code=500, detail="Error creating video generation job")
    finally:
        db.close()
    
    # Process the job in the background
    # In a real implementation, you might use a proper task queue like Celery
    # For this implementation, we'll start an async task
    logger.info(f"Created job {job_id} for video generation")
    
    # Start the video generation workflow in the background
    workflow = VideoGenerationWorkflow()
    
    # Create input data for the workflow
    input_data = {
        "input_file_path": video_path,
        "description_text": description_text,
        "target_language": target_language,
        "job_id": job_id
    }
    
    # Run the workflow in the background
    # Note: In production, you'd want to use a proper task queue like Celery
    import asyncio
    asyncio.create_task(run_video_generation_workflow(input_data, job_id))
    
    # Return the job details
    db = next(get_db())
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse.from_orm(job) if hasattr(JobResponse, 'from_orm') else JobResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            input_file_path=job.input_file_path,
            output_file_path=job.output_file_path,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
    finally:
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
async def get_job_status(job_id: int):
    """
    Get the status of a video generation job
    """
    db = next(get_db())
    try:
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
    finally:
        db.close()


@router.post("/upload", response_model=UploadResponse)
async def upload_video(video_file: UploadFile = File(...)):
    """
    Upload a video file without starting generation
    """
    # Validate file type
    file_extension = video_file.filename.split(".")[-1].lower()
    if file_extension not in settings.allowed_video_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed formats: {settings.allowed_video_formats}"
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
async def list_jobs(status: Optional[str] = None, limit: int = 100, offset: int = 0):
    """
    List video generation jobs with optional filtering
    """
    db = next(get_db())
    try:
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
    finally:
        db.close()


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int):
    """
    Delete a video generation job
    """
    db = next(get_db())
    try:
        job_tracker = JobTracker(db)
        success = job_tracker.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": f"Job {job_id} deleted successfully"}
    finally:
        db.close()