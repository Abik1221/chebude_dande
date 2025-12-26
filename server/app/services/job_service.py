from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import os
from app.models.job import Job
from app.schemas.request import JobStatus
from app.config import settings
from loguru import logger


class JobTracker:
    """
    Service for tracking and managing video generation jobs
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(self, input_file_path: str, description_text: str, target_language: str) -> Job:
        """
        Create a new video generation job
        """
        job = Job(
            status=JobStatus.PENDING.value,
            input_file_path=input_file_path,
            description_text=description_text,
            target_language=target_language,
            progress=0
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Created new job with ID: {job.id}")
        return job
    
    def update_job_status(self, job_id: int, status: JobStatus, progress: Optional[int] = None, 
                         error_message: Optional[str] = None, output_file_path: Optional[str] = None) -> Job:
        """
        Update job status and other attributes
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        job.status = status.value if isinstance(status, JobStatus) else status
        job.updated_at = datetime.utcnow()
        
        if progress is not None:
            job.progress = progress
        
        if error_message is not None:
            job.error_message = error_message
        
        if output_file_path is not None:
            job.output_file_path = output_file_path
        
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Updated job {job_id} status to {job.status}, progress: {job.progress}%")
        return job
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """
        Get job by ID
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        return job
    
    def get_job_status(self, job_id: int) -> Optional[Job]:
        """
        Get job status by ID
        """
        return self.get_job(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100, offset: int = 0) -> List[Job]:
        """
        List jobs with optional filtering by status
        """
        query = self.db.query(Job)
        
        if status:
            query = query.filter(Job.status == status.value if isinstance(status, JobStatus) else status)
        
        jobs = query.offset(offset).limit(limit).all()
        return jobs
    
    def delete_job(self, job_id: int) -> bool:
        """
        Delete a job by ID
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False
        
        self.db.delete(job)
        self.db.commit()
        logger.info(f"Deleted job with ID: {job_id}")
        return True
    
    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """
        Clean up completed jobs older than specified days
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_jobs = self.db.query(Job).filter(
            Job.status == JobStatus.COMPLETED.value,
            Job.updated_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for job in old_jobs:
            # Delete associated files if they exist
            if job.input_file_path and os.path.exists(job.input_file_path):
                try:
                    os.remove(job.input_file_path)
                    logger.info(f"Deleted input file for job {job.id}: {job.input_file_path}")
                except Exception as e:
                    logger.error(f"Error deleting input file for job {job.id}: {e}")
            
            if job.output_file_path and os.path.exists(job.output_file_path):
                try:
                    os.remove(job.output_file_path)
                    logger.info(f"Deleted output file for job {job.id}: {job.output_file_path}")
                except Exception as e:
                    logger.error(f"Error deleting output file for job {job.id}: {e}")
            
            # Delete the job record
            self.db.delete(job)
            deleted_count += 1
        
        self.db.commit()
        logger.info(f"Cleaned up {deleted_count} old jobs")
        return deleted_count


# Global job tracker instance (in production, you'd want to use dependency injection)
def get_job_tracker(db: Session) -> JobTracker:
    """
    Get job tracker instance with database session
    """
    return JobTracker(db)