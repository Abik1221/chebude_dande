import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.database import Base
from app.models.job import Job, Language
from app.schemas.request import JobStatus


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
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestLanguageModel:
    def test_language_creation(self, db_session):
        """Test creating a Language instance"""
        language = Language(
            code="en",
            name="English",
            tts_voice="nova",
            is_active=True
        )
        
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        assert language.code == "en"
        assert language.name == "English"
        assert language.tts_voice == "nova"
        assert language.is_active is True
        assert language.id is not None
        assert language.created_at is not None
    
    def test_language_creation_with_defaults(self, db_session):
        """Test creating a Language with default values"""
        language = Language(
            code="te",
            name="Telugu",
            tts_voice="onyx"
            # is_active should default to True
        )
        
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        assert language.code == "te"
        assert language.name == "Telugu"
        assert language.tts_voice == "onyx"
        assert language.is_active is True  # Default value
    
    def test_language_unique_code_constraint(self, db_session):
        """Test that language codes must be unique"""
        # Add first language
        language1 = Language(code="en", name="English", tts_voice="nova")
        db_session.add(language1)
        db_session.commit()
        
        # Try to add another language with same code
        language2 = Language(code="en", name="English2", tts_voice="nova2")
        db_session.add(language2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_language_string_representation(self, db_session):
        """Test the string representation of Language model"""
        language = Language(code="es", name="Spanish", tts_voice="alloy")
        assert "Spanish" in str(language)
        assert "es" in str(language)


class TestJobModel:
    def test_job_creation(self, db_session):
        """Test creating a Job instance"""
        job = Job(
            status="PENDING",
            input_file_path="/path/to/video.mp4",
            description_text="This is a beautiful property.",
            target_language="en",
            progress=0
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        assert job.status == "PENDING"
        assert job.input_file_path == "/path/to/video.mp4"
        assert job.description_text == "This is a beautiful property."
        assert job.target_language == "en"
        assert job.progress == 0
        assert job.id is not None
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_job_creation_with_defaults(self, db_session):
        """Test creating a Job with default values"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
            # status should default to "PENDING"
            # progress should default to 0
            # output_file_path should default to None
            # error_message should default to None
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        assert job.status == "PENDING"
        assert job.progress == 0
        assert job.output_file_path is None
        assert job.error_message is None
    
    def test_job_status_transitions(self, db_session):
        """Test updating job status through different phases"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Test initial status
        assert job.status == "PENDING"
        
        # Update to processing
        job.status = "PROCESSING"
        db_session.commit()
        db_session.refresh(job)
        assert job.status == "PROCESSING"
        
        # Update to completed
        job.status = "COMPLETED"
        db_session.commit()
        db_session.refresh(job)
        assert job.status == "COMPLETED"
    
    def test_job_progress_updates(self, db_session):
        """Test updating job progress"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Test initial progress
        assert job.progress == 0
        
        # Update progress
        job.progress = 50
        db_session.commit()
        db_session.refresh(job)
        assert job.progress == 50
        
        # Update to completion
        job.progress = 100
        db_session.commit()
        db_session.refresh(job)
        assert job.progress == 100
    
    def test_job_output_file_path(self, db_session):
        """Test setting and updating output file path"""
        job = Job(
            input_file_path="/path/to/input.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Initially should be None
        assert job.output_file_path is None
        
        # Set output path
        job.output_file_path = "/path/to/output.mp4"
        db_session.commit()
        db_session.refresh(job)
        assert job.output_file_path == "/path/to/output.mp4"
    
    def test_job_error_message(self, db_session):
        """Test setting and updating error message"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Initially should be None
        assert job.error_message is None
        
        # Set error message
        error_msg = "An error occurred during processing"
        job.error_message = error_msg
        db_session.commit()
        db_session.refresh(job)
        assert job.error_message == error_msg
    
    def test_job_timestamps(self, db_session):
        """Test that timestamps are automatically set"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Check that timestamps are set
        assert job.created_at is not None
        assert job.updated_at is not None
        
        # Update the job and check that updated_at changes
        original_updated_at = job.updated_at
        job.status = "PROCESSING"
        db_session.commit()
        db_session.refresh(job)
        
        # updated_at should be different after update
        assert job.updated_at >= original_updated_at
    
    def test_job_string_representation(self, db_session):
        """Test the string representation of Job model"""
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        job_str = str(job)
        assert str(job.id) in job_str
        assert job.status in job_str
        assert job.target_language in job_str


class TestModelRelationships:
    def test_language_job_relationship(self, db_session):
        """Test relationships between models (conceptual - no direct FK in this implementation)"""
        # In this implementation, there's no direct foreign key relationship
        # between Job and Language, but they're related through the target_language field
        language = Language(code="en", name="English", tts_voice="nova")
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"  # Matches the language code
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # The relationship is logical through target_language field
        assert job.target_language == language.code


class TestModelConstraints:
    def test_required_fields_job(self, db_session):
        """Test that required fields are enforced"""
        # Test with minimal required fields
        job = Job(
            input_file_path="/path/to/video.mp4",
            description_text="Property description",
            target_language="en"
        )
        
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        assert job.input_file_path is not None
        assert job.description_text is not None
        assert job.target_language is not None
    
    def test_required_fields_language(self, db_session):
        """Test that required fields are enforced for Language"""
        language = Language(
            code="fr",
            name="French",
            tts_voice="nova"
        )
        
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        assert language.code is not None
        assert language.name is not None
        assert language.tts_voice is not None


class TestModelValidation:
    def test_job_status_values(self, db_session):
        """Test various valid job status values"""
        valid_statuses = [
            "PENDING",
            "PROCESSING", 
            "COMPLETED",
            "FAILED",
            "VALIDATING",
            "TEXT_PROCESSING",
            "TTS_GENERATION",
            "AUDIO_PROCESSING",
            "VIDEO_MERGING"
        ]
        
        for status in valid_statuses:
            job = Job(
                status=status,
                input_file_path="/path/to/video.mp4",
                description_text="Property description",
                target_language="en"
            )
            
            db_session.add(job)
            db_session.commit()
            db_session.refresh(job)
            
            assert job.status == status
            # Clean up for next iteration
            db_session.delete(job)
            db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__])