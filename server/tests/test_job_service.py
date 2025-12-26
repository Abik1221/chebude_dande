import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.services.job_service import JobTracker, get_job_tracker
from app.models.job import Job
from app.schemas.request import JobStatus
import os
import tempfile


# Create a temporary database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a database session for testing"""
    # Create all tables
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def job_tracker(db_session):
    """Create a JobTracker instance for testing"""
    return JobTracker(db_session)


class TestJobTrackerInitialization:
    def test_job_tracker_initialization(self, db_session):
        """Test successful initialization of JobTracker"""
        tracker = JobTracker(db_session)
        assert tracker.db == db_session


class TestCreateJob:
    def test_create_job_success(self, job_tracker, db_session):
        """Test successful job creation"""
        job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="This is a beautiful property with great amenities.",
            target_language="en"
        )
        
        # Verify the job was created with correct attributes
        assert job.status == "PENDING"
        assert job.input_file_path == "/path/to/video.mp4"
        assert job.description_text == "This is a beautiful property with great amenities."
        assert job.target_language == "en"
        assert job.progress == 0
        assert job.id is not None
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_create_job_defaults(self, job_tracker, db_session):
        """Test that default values are set correctly during job creation"""
        job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="te"
        )
        
        # Verify defaults
        assert job.status == "PENDING"
        assert job.progress == 0
        assert job.output_file_path is None
        assert job.error_message is None


class TestUpdateJobStatus:
    def test_update_job_status_success(self, job_tracker, db_session):
        """Test successful job status update"""
        # Create a job first
        job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Update the job status
        updated_job = job_tracker.update_job_status(
            job_id=job.id,
            status="PROCESSING",
            progress=50
        )
        
        # Verify the update
        assert updated_job.status == "PROCESSING"
        assert updated_job.progress == 50
        assert updated_job.id == job.id
    
    def test_update_job_status_with_all_params(self, job_tracker, db_session):
        """Test updating job with all parameters"""
        # Create a job first
        job = job_tracker.create_job(
            input_file_path="/path/to/input.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Update the job with all parameters
        updated_job = job_tracker.update_job_status(
            job_id=job.id,
            status="COMPLETED",
            progress=100,
            error_message=None,
            output_file_path="/path/to/output.mp4"
        )
        
        # Verify all updates
        assert updated_job.status == "COMPLETED"
        assert updated_job.progress == 100
        assert updated_job.output_file_path == "/path/to/output.mp4"
        assert updated_job.error_message is None
    
    def test_update_job_status_with_error(self, job_tracker, db_session):
        """Test updating job status with error message"""
        # Create a job first
        job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Update the job with error
        error_msg = "Processing failed due to invalid video format"
        updated_job = job_tracker.update_job_status(
            job_id=job.id,
            status="FAILED",
            progress=30,
            error_message=error_msg
        )
        
        # Verify the update
        assert updated_job.status == "FAILED"
        assert updated_job.progress == 30
        assert updated_job.error_message == error_msg
    
    def test_update_nonexistent_job(self, job_tracker):
        """Test updating a non-existent job"""
        with pytest.raises(ValueError, match="Job with ID 999999 not found"):
            job_tracker.update_job_status(
                job_id=999999,
                status="PROCESSING"
            )


class TestGetJob:
    def test_get_job_success(self, job_tracker, db_session):
        """Test getting an existing job"""
        # Create a job first
        original_job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Get the job
        retrieved_job = job_tracker.get_job(original_job.id)
        
        # Verify the retrieved job matches the original
        assert retrieved_job.id == original_job.id
        assert retrieved_job.status == original_job.status
        assert retrieved_job.input_file_path == original_job.input_file_path
        assert retrieved_job.description_text == original_job.description_text
        assert retrieved_job.target_language == original_job.target_language
    
    def test_get_nonexistent_job(self, job_tracker):
        """Test getting a non-existent job"""
        result = job_tracker.get_job(999999)
        assert result is None


class TestGetJobStatus:
    def test_get_job_status_success(self, job_tracker, db_session):
        """Test getting job status for existing job"""
        # Create a job first
        original_job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Update the job to change status
        job_tracker.update_job_status(
            job_id=original_job.id,
            status="PROCESSING",
            progress=25
        )
        
        # Get the job status
        status_job = job_tracker.get_job_status(original_job.id)
        
        # Verify the status
        assert status_job.id == original_job.id
        assert status_job.status == "PROCESSING"
        assert status_job.progress == 25
    
    def test_get_job_status_nonexistent(self, job_tracker):
        """Test getting status for non-existent job"""
        result = job_tracker.get_job_status(999999)
        assert result is None


class TestListJobs:
    def test_list_jobs_no_filter(self, job_tracker, db_session):
        """Test listing all jobs without filter"""
        # Create multiple jobs
        job1 = job_tracker.create_job(
            input_file_path="/path/to/video1.mp4",
            description_text="Property 1",
            target_language="en"
        )
        job2 = job_tracker.create_job(
            input_file_path="/path/to/video2.mp4",
            description_text="Property 2",
            target_language="te"
        )
        
        # List all jobs
        jobs = job_tracker.list_jobs()
        
        # Verify both jobs are returned
        assert len(jobs) == 2
        job_ids = [job.id for job in jobs]
        assert job1.id in job_ids
        assert job2.id in job_ids
    
    def test_list_jobs_with_status_filter(self, job_tracker, db_session):
        """Test listing jobs with status filter"""
        # Create jobs with different statuses
        job1 = job_tracker.create_job(
            input_file_path="/path/to/video1.mp4",
            description_text="Property 1",
            target_language="en"
        )
        
        job2 = job_tracker.create_job(
            input_file_path="/path/to/video2.mp4",
            description_text="Property 2",
            target_language="te"
        )
        # Update job2 to different status
        job_tracker.update_job_status(job2.id, "PROCESSING")
        
        # List jobs with PENDING status
        pending_jobs = job_tracker.list_jobs(status="PENDING")
        processing_jobs = job_tracker.list_jobs(status="PROCESSING")
        
        # Verify filtering works
        assert len(pending_jobs) == 1
        assert pending_jobs[0].id == job1.id
        assert len(processing_jobs) == 1
        assert processing_jobs[0].id == job2.id
    
    def test_list_jobs_with_limit_and_offset(self, job_tracker, db_session):
        """Test listing jobs with limit and offset"""
        # Create multiple jobs
        for i in range(5):
            job_tracker.create_job(
                input_file_path=f"/path/to/video{i}.mp4",
                description_text=f"Property {i}",
                target_language="en"
            )
        
        # List jobs with limit
        limited_jobs = job_tracker.list_jobs(limit=3)
        assert len(limited_jobs) == 3
        
        # List jobs with offset
        offset_jobs = job_tracker.list_jobs(limit=3, offset=2)
        assert len(offset_jobs) <= 3  # Could be less if there aren't enough jobs


class TestDeleteJob:
    def test_delete_job_success(self, job_tracker, db_session):
        """Test successful job deletion"""
        # Create a job first
        job = job_tracker.create_job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        # Verify job exists
        retrieved_job = job_tracker.get_job(job.id)
        assert retrieved_job is not None
        
        # Delete the job
        success = job_tracker.delete_job(job.id)
        
        # Verify deletion
        assert success is True
        deleted_job = job_tracker.get_job(job.id)
        assert deleted_job is None
    
    def test_delete_nonexistent_job(self, job_tracker):
        """Test deleting a non-existent job"""
        success = job_tracker.delete_job(999999)
        assert success is False


class TestCleanupOldJobs:
    def test_cleanup_old_jobs(self, job_tracker, db_session):
        """Test cleaning up old completed jobs"""
        # Create a completed job with old timestamp
        old_job = Job(
            status="COMPLETED",
            input_file_path="/path/to/old_video.mp4",
            description_text="Old property description",
            target_language="en",
            created_at=datetime.utcnow() - timedelta(days=10),  # 10 days old
            updated_at=datetime.utcnow() - timedelta(days=10)
        )
        db_session.add(old_job)
        db_session.commit()
        db_session.refresh(old_job)
        
        # Create a recent completed job
        recent_job = Job(
            status="COMPLETED",
            input_file_path="/path/to/recent_video.mp4",
            description_text="Recent property description",
            target_language="en",
            created_at=datetime.utcnow() - timedelta(days=2),  # 2 days old
            updated_at=datetime.utcnow() - timedelta(days=2)
        )
        db_session.add(recent_job)
        db_session.commit()
        db_session.refresh(recent_job)
        
        # Create a recent pending job (should not be deleted)
        pending_job = Job(
            status="PENDING",
            input_file_path="/path/to/pending_video.mp4",
            description_text="Pending property description",
            target_language="en",
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(days=2)
        )
        db_session.add(pending_job)
        db_session.commit()
        db_session.refresh(pending_job)
        
        # Run cleanup (remove jobs older than 7 days)
        deleted_count = job_tracker.cleanup_old_jobs(days_old=7)
        
        # Verify cleanup
        assert deleted_count == 1  # Only the old completed job should be deleted
        
        # Check that old job is deleted
        old_job_check = job_tracker.get_job(old_job.id)
        assert old_job_check is None
        
        # Check that recent jobs still exist
        recent_job_check = job_tracker.get_job(recent_job.id)
        assert recent_job_check is not None
        pending_job_check = job_tracker.get_job(pending_job.id)
        assert pending_job_check is not None


class TestFileOperationsInCleanup:
    def test_cleanup_deletes_associated_files(self, job_tracker, db_session):
        """Test that cleanup also deletes associated files"""
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file_path = input_file.name
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_file_path = output_file.name
        
        try:
            # Create a completed job with file paths
            old_job = Job(
                status="COMPLETED",
                input_file_path=input_file_path,
                output_file_path=output_file_path,
                description_text="Old property description",
                target_language="en",
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow() - timedelta(days=10)
            )
            db_session.add(old_job)
            db_session.commit()
            db_session.refresh(old_job)
            
            # Verify files exist before cleanup
            assert os.path.exists(input_file_path)
            assert os.path.exists(output_file_path)
            
            # Run cleanup
            deleted_count = job_tracker.cleanup_old_jobs(days_old=7)
            
            # Verify cleanup occurred
            assert deleted_count == 1
            
            # Verify files were also deleted
            assert not os.path.exists(input_file_path)
            assert not os.path.exists(output_file_path)
            
        finally:
            # Clean up any remaining files
            for path in [input_file_path, output_file_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass  # File might already be deleted


class TestGetJobTrackerFunction:
    def test_get_job_tracker_function(self, db_session):
        """Test the get_job_tracker function"""
        tracker = get_job_tracker(db_session)
        assert isinstance(tracker, JobTracker)
        assert tracker.db == db_session


if __name__ == "__main__":
    pytest.main([__file__])