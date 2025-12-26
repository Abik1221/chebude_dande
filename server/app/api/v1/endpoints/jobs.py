from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.workflows.video_generation import compiled_workflow
from app.services.tts_service import TTSManager
from app.services.video_service import VideoProcessor
import os
import tempfile
from datetime import datetime

router = APIRouter()


@router.get("/status/{job_id}", response_model=JobResponse, summary="Get job status")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a video generation job
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        output_file_path=job.output_file_path
    )


@router.get("/jobs", response_model=List[JobResponse], summary="Get all jobs")
async def get_all_jobs(db: Session = Depends(get_db)):
    """
    Get all video generation jobs
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        JobResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            output_file_path=job.output_file_path
        ) for job in jobs
    ]


@router.delete("/jobs/{job_id}", summary="Delete a job")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete a video generation job
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}


@router.post("/upload", summary="Upload video file without starting generation")
async def upload_video(video_file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a video file without starting generation
    """
    # Validate video file
    allowed_extensions = [".mp4", ".mov", ".avi", ".mkv", ".wmv"]
    file_extension = os.path.splitext(video_file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid video file format")
    
    # Check file size (max 100MB)
    video_file.file.seek(0, 2)  # Seek to end
    file_size = video_file.file.tell()
    video_file.file.seek(0)  # Seek back to beginning
    
    max_size_mb = 100  # From settings
    if file_size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {max_size_mb}MB limit")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        contents = await video_file.read()
        temp_file.write(contents)
        file_path = temp_file.name
    
    return {
        "filename": video_file.filename,
        "size": file_size,
        "path": file_path
    }