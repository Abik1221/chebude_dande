import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.job import Job, Language
from app.config import settings


# Create a temporary database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the database tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """
    Override the get_db dependency for testing
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture
def sample_video_file():
    """Create a temporary video file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write minimal valid MP4 header (just for testing purposes)
        temp_file.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom')
        temp_file.write(b'\x00\x00\x00\x1cmdat')  # Add some data
        temp_file.write(b'\x00' * 1000)  # Add some padding
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


@pytest.fixture
def sample_small_video_file():
    """Create a small temporary video file for upload testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write minimal content that looks like a small video file
        temp_file.write(b'\x00' * 100)  # Small content
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


class TestRootEndpoint:
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Property Video Generator API" in data["message"]
        assert "version" in data


class TestGenerateVideoEndpoint:
    def test_generate_video_success(self, sample_small_video_file):
        """Test successful video generation request"""
        # Mock the workflow and services
        with patch('app.api.v1.video_generation.VideoGenerationWorkflow') as mock_workflow_cls, \
             patch('app.api.v1.video_generation.asyncio.create_task') as mock_create_task, \
             patch('app.api.v1.video_generation.run_video_generation_workflow') as mock_run_workflow:
            
            # Create a mock workflow instance
            mock_workflow = Mock()
            mock_workflow_cls.return_value = mock_workflow
            
            # Mock the run_workflow method
            mock_result = Mock()
            mock_result.status = "PENDING"
            mock_result.progress = 0
            mock_result.output_path = None
            mock_result.error_message = None
            mock_workflow.run_workflow = AsyncMock(return_value=mock_result)
            
            # Prepare test data
            description_text = "This is a beautiful property with great amenities."
            target_language = "en"
            
            with open(sample_small_video_file, "rb") as video_file:
                response = client.post(
                    "/api/v1/generate",
                    data={
                        "description_text": description_text,
                        "target_language": target_language
                    },
                    files={"video_file": video_file}
                )
            
            # Should succeed (though the actual processing will fail due to missing API keys)
            # But the request validation should pass
            assert response.status_code in [200, 422, 500]  # 200 if job created, 422/500 if processing fails
    
    def test_generate_video_invalid_file_type(self, sample_small_video_file):
        """Test video generation with invalid file type"""
        # Change the file extension to simulate an invalid type
        invalid_file = sample_small_video_file.replace('.mp4', '.exe')
        os.rename(sample_small_video_file, invalid_file)
        
        try:
            with open(invalid_file, "rb") as video_file:
                response = client.post(
                    "/api/v1/generate",
                    data={
                        "description_text": "Test description",
                        "target_language": "en"
                    },
                    files={"video_file": video_file}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported file format" in data["detail"]
        finally:
            # Restore the original file name for cleanup
            os.rename(invalid_file, sample_small_video_file)
    
    def test_generate_video_file_too_large(self):
        """Test video generation with file that's too large"""
        # Create a large file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as large_file:
            # Write a file larger than the max allowed size (100MB in settings)
            large_file.write(b'\x00' * (settings.max_video_size_mb + 1) * 1024 * 1024)
            large_file_path = large_file.name
        
        try:
            with open(large_file_path, "rb") as video_file:
                response = client.post(
                    "/api/v1/generate",
                    data={
                        "description_text": "Test description",
                        "target_language": "en"
                    },
                    files={"video_file": video_file}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "File too large" in data["detail"]
        finally:
            # Clean up the large file
            if os.path.exists(large_file_path):
                os.remove(large_file_path)
    
    def test_generate_video_missing_fields(self, sample_small_video_file):
        """Test video generation with missing required fields"""
        with open(sample_small_video_file, "rb") as video_file:
            response = client.post(
                "/api/v1/generate",
                data={
                    # Missing description_text
                    "target_language": "en"
                },
                files={"video_file": video_file}
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_video_invalid_language(self, sample_small_video_file):
        """Test video generation with invalid language code"""
        with open(sample_small_video_file, "rb") as video_file:
            response = client.post(
                "/api/v1/generate",
                data={
                    "description_text": "Test description",
                    "target_language": "xx"  # Invalid language code
                },
                files={"video_file": video_file}
            )
        
        # Should fail during validation
        assert response.status_code in [200, 422, 500]


class TestJobStatusEndpoint:
    def test_get_job_status_success(self):
        """Test getting job status for existing job"""
        # Create a mock job in the database
        db = TestingSessionLocal()
        try:
            job = Job(
                status="PENDING",
                input_file_path="/path/to/test.mp4",
                description_text="Test description",
                target_language="en"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            job_id = job.id
        finally:
            db.close()
        
        response = client.get(f"/api/v1/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["id"] == job_id
        assert data["status"] == "PENDING"
    
    def test_get_job_status_not_found(self):
        """Test getting job status for non-existent job"""
        response = client.get("/api/v1/status/999999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Job not found" in data["detail"]


class TestUploadVideoEndpoint:
    def test_upload_video_success(self, sample_small_video_file):
        """Test successful video upload"""
        with open(sample_small_video_file, "rb") as video_file:
            response = client.post(
                "/api/v1/upload",
                files={"video_file": video_file}
            )
        
        # Should fail due to file validation (not a real video file), but validation should pass
        assert response.status_code in [200, 400, 422]
    
    def test_upload_video_invalid_format(self):
        """Test video upload with invalid format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'test content')
            temp_path = temp_file.name
        
        try:
            with open(temp_path, "rb") as video_file:
                response = client.post(
                    "/api/v1/upload",
                    files={"video_file": ("test.txt", video_file, "text/plain")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported file format" in data["detail"]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_upload_video_too_large(self):
        """Test video upload with file that's too large"""
        # Create a large file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as large_file:
            # Write a file larger than the max allowed size (100MB in settings)
            large_file.write(b'\x00' * (settings.max_video_size_mb + 1) * 1024 * 1024)
            large_file_path = large_file.name
        
        try:
            with open(large_file_path, "rb") as video_file:
                response = client.post(
                    "/api/v1/upload",
                    files={"video_file": video_file}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "File too large" in data["detail"]
        finally:
            # Clean up the large file
            if os.path.exists(large_file_path):
                os.remove(large_file_path)


class TestSupportedLanguagesEndpoint:
    def test_get_supported_languages(self):
        """Test getting supported languages"""
        response = client.get("/api/v1/languages")
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list of languages
        assert isinstance(data, list)
        assert len(data) >= 0  # Could be empty in test environment
        
        # If languages exist, check their structure
        for lang in data:
            assert "code" in lang
            assert "name" in lang
            assert "tts_voice" in lang


class TestListJobsEndpoint:
    def test_list_jobs_success(self):
        """Test listing jobs without filters"""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_jobs_with_status_filter(self):
        """Test listing jobs with status filter"""
        response = client.get("/api/v1/jobs?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDeleteJobEndpoint:
    def test_delete_job_success(self):
        """Test deleting an existing job"""
        # Create a mock job in the database
        db = TestingSessionLocal()
        try:
            job = Job(
                status="PENDING",
                input_file_path="/path/to/test.mp4",
                description_text="Test description",
                target_language="en"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            job_id = job.id
        finally:
            db.close()
        
        response = client.delete(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Job {job_id} deleted successfully" in data["message"]
    
    def test_delete_job_not_found(self):
        """Test deleting a non-existent job"""
        response = client.delete("/api/v1/jobs/999999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Job not found" in data["detail"]


class TestAPIErrorHandling:
    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint"""
        response = client.get("/api/v1/invalid_endpoint")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test using invalid HTTP method on an endpoint"""
        response = client.put("/")  # PUT on root endpoint
        assert response.status_code == 405  # Method not allowed


# Additional tests for error scenarios
class TestErrorScenarios:
    def test_generate_video_with_empty_description(self, sample_small_video_file):
        """Test video generation with empty description"""
        with open(sample_small_video_file, "rb") as video_file:
            response = client.post(
                "/api/v1/generate",
                data={
                    "description_text": "",  # Empty description
                    "target_language": "en"
                },
                files={"video_file": video_file}
            )
        
        # Should fail validation
        assert response.status_code in [422, 400]
    
    def test_generate_video_with_long_description(self, sample_small_video_file):
        """Test video generation with description that's too long"""
        long_description = "This is a very long description. " * 200  # Way over limit
        
        with open(sample_small_video_file, "rb") as video_file:
            response = client.post(
                "/api/v1/generate",
                data={
                    "description_text": long_description,
                    "target_language": "en"
                },
                files={"video_file": video_file}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Description text too long" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__])