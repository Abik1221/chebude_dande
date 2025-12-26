import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.workflows.video_generation import VideoGenerationWorkflow, VideoGenerationState
from app.services.tts_service import TTSServiceManager
from app.services.video_service import VideoProcessingService


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
def sample_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        # Write minimal valid MP3 header (just for testing purposes)
        temp_file.write(b'\xff\xfb\x90\x00')  # MP3 sync word and header
        temp_file.write(b'\x00' * 1000)  # Add some padding
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


@pytest.fixture
def sample_processed_audio_file():
    """Create a temporary processed audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        # Write minimal valid MP3 header (just for testing purposes)
        temp_file.write(b'\xff\xfb\x90\x00')  # MP3 sync word and header
        temp_file.write(b'\x00' * 1000)  # Add some padding
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


class TestVideoGenerationState:
    def test_state_initialization(self):
        """Test initialization of VideoGenerationState"""
        state = VideoGenerationState()
        
        assert state.input_data == {}
        assert state.status == "PENDING"
        assert state.progress == 0
        assert state.error_message is None
        assert state.temp_files == []
        assert state.output_path is None


class TestVideoGenerationWorkflow:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup common mocks for all tests"""
        # Mock the services
        self.mock_tts_service = Mock(spec=TTSServiceManager)
        self.mock_video_service = Mock(spec=VideoProcessingService)
        
        # Patch the services in the workflow
        with patch('app.workflows.video_generation.TTSServiceManager') as mock_tts_cls, \
             patch('app.workflows.video_generation.VideoProcessingService') as mock_video_cls:
            
            mock_tts_cls.return_value = self.mock_tts_service
            mock_video_cls.return_value = self.mock_video_service
            
            yield
    
    def test_workflow_initialization(self):
        """Test successful initialization of VideoGenerationWorkflow"""
        workflow = VideoGenerationWorkflow()
        
        assert workflow is not None
        assert workflow.tts_service == self.mock_tts_service
        assert workflow.video_service == self.mock_video_service
        assert workflow.workflow is not None
    
    @pytest.mark.asyncio
    async def test_validate_input_success(self, sample_video_file):
        """Test successful input validation"""
        workflow = VideoGenerationWorkflow()
        
        # Mock video format validation
        self.mock_video_service.validate_video_format = AsyncMock(return_value=True)
        
        # Create state with valid input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "description_text": "This is a test property with beautiful amenities.",
            "target_language": "en"
        }
        
        result_state = await workflow._validate_input(state)
        
        assert result_state.status == "TEXT_PROCESSING"
        assert result_state.progress == 10
        assert result_state.error_message is None
    
    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self):
        """Test input validation with missing required fields"""
        workflow = VideoGenerationWorkflow()
        
        # Create state with missing fields
        state = VideoGenerationState()
        state.input_data = {
            # Missing required fields
        }
        
        result_state = await workflow._validate_input(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Missing required field" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_validate_input_invalid_video_file(self):
        """Test input validation with non-existent video file"""
        workflow = VideoGenerationWorkflow()
        
        # Create state with non-existent file
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": "/non/existent/video.mp4",
            "description_text": "This is a test property with beautiful amenities.",
            "target_language": "en"
        }
        
        result_state = await workflow._validate_input(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Video file does not exist" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_validate_input_unsupported_format(self, sample_video_file):
        """Test input validation with unsupported video format"""
        workflow = VideoGenerationWorkflow()
        
        # Mock video format validation to return False
        self.mock_video_service.validate_video_format = AsyncMock(return_value=False)
        
        # Create state with unsupported format
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "description_text": "This is a test property with beautiful amenities.",
            "target_language": "en"
        }
        
        result_state = await workflow._validate_input(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Unsupported video format" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_validate_input_text_too_long(self, sample_video_file):
        """Test input validation with text that is too long"""
        workflow = VideoGenerationWorkflow()
        
        # Mock video format validation
        self.mock_video_service.validate_video_format = AsyncMock(return_value=True)
        
        # Create state with text that is too long
        long_text = "This is a very long description. " * 200  # Way over limit
        
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "description_text": long_text,
            "target_language": "en"
        }
        
        result_state = await workflow._validate_input(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Description text too long" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_process_text_success(self):
        """Test successful text processing"""
        workflow = VideoGenerationWorkflow()
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "description_text": "  This   is   a   test   property.  ",
            "target_language": "en"
        }
        
        result_state = await workflow._process_text(state)
        
        assert result_state.status == "TTS_GENERATION"
        assert result_state.progress == 30
        assert result_state.error_message is None
        # Verify text was cleaned
        assert "cleaned_description" in result_state.input_data
        assert result_state.input_data["cleaned_description"] == "This is a test property."
    
    @pytest.mark.asyncio
    async def test_process_text_failure(self):
        """Test text processing failure"""
        workflow = VideoGenerationWorkflow()
        
        # Create state with no input data (should cause error)
        state = VideoGenerationState()
        state.input_data = {}
        
        result_state = await workflow._process_text(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
    
    @pytest.mark.asyncio
    async def test_generate_audio_success(self, sample_video_file, sample_audio_file):
        """Test successful audio generation"""
        workflow = VideoGenerationWorkflow()
        
        # Mock the TTS service to return success
        self.mock_tts_service.generate_audio = AsyncMock(return_value=sample_audio_file)
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "cleaned_description": "This is a test property with beautiful amenities.",
            "target_language": "en"
        }
        
        result_state = await workflow._generate_audio(state)
        
        assert result_state.status == "AUDIO_PROCESSING"
        assert result_state.progress == 60
        assert result_state.error_message is None
        assert "audio_file_path" in result_state.input_data
        assert result_state.input_data["audio_file_path"] == sample_audio_file
        
        # Verify TTS service was called with correct parameters
        self.mock_tts_service.generate_audio.assert_called_once_with(
            text="This is a test property with beautiful amenities.",
            language_code="en",
            output_path=sample_audio_file
        )
    
    @pytest.mark.asyncio
    async def test_generate_audio_failure(self, sample_video_file):
        """Test audio generation failure"""
        workflow = VideoGenerationWorkflow()
        
        # Mock the TTS service to raise an exception
        self.mock_tts_service.generate_audio = AsyncMock(side_effect=Exception("TTS Error"))
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "cleaned_description": "This is a test property with beautiful amenities.",
            "target_language": "en"
        }
        
        result_state = await workflow._generate_audio(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "TTS Error" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_process_audio_success(self, sample_video_file, sample_audio_file, sample_processed_audio_file):
        """Test successful audio processing"""
        workflow = VideoGenerationWorkflow()
        
        # Mock duration extraction
        self.mock_video_service.extract_video_duration = AsyncMock(return_value=120.0)
        self.mock_video_service.extract_audio_duration = AsyncMock(return_value=100.0)
        
        # Mock audio adjustment
        self.mock_video_service.adjust_audio_to_video_duration = AsyncMock(return_value=sample_processed_audio_file)
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "audio_file_path": sample_audio_file
        }
        
        result_state = await workflow._process_audio(state)
        
        assert result_state.status == "VIDEO_MERGING"
        assert result_state.progress == 80
        assert result_state.error_message is None
        assert "processed_audio_path" in result_state.input_data
        assert result_state.input_data["processed_audio_path"] == sample_processed_audio_file
    
    @pytest.mark.asyncio
    async def test_process_audio_failure(self, sample_video_file, sample_audio_file):
        """Test audio processing failure"""
        workflow = VideoGenerationWorkflow()
        
        # Mock duration extraction to raise an error
        self.mock_video_service.extract_video_duration = AsyncMock(side_effect=Exception("Duration Error"))
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "audio_file_path": sample_audio_file
        }
        
        result_state = await workflow._process_audio(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Duration Error" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_merge_video_success(self, sample_video_file, sample_processed_audio_file):
        """Test successful video merging"""
        workflow = VideoGenerationWorkflow()
        
        # Mock video merging
        self.mock_video_service.merge_audio_video = AsyncMock(return_value="/path/to/output.mp4")
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "processed_audio_path": sample_processed_audio_file
        }
        
        result_state = await workflow._merge_video(state)
        
        assert result_state.status == "COMPLETED"
        assert result_state.progress == 100
        assert result_state.error_message is None
        assert result_state.output_path == "/path/to/output.mp4"
    
    @pytest.mark.asyncio
    async def test_merge_video_failure(self, sample_video_file, sample_processed_audio_file):
        """Test video merging failure"""
        workflow = VideoGenerationWorkflow()
        
        # Mock video merging to raise an error
        self.mock_video_service.merge_audio_video = AsyncMock(side_effect=Exception("Merge Error"))
        
        # Create state with input data
        state = VideoGenerationState()
        state.input_data = {
            "input_file_path": sample_video_file,
            "processed_audio_path": sample_processed_audio_file
        }
        
        result_state = await workflow._merge_video(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message is not None
        assert "Merge Error" in result_state.error_message
    
    @pytest.mark.asyncio
    async def test_handle_error_success(self, sample_audio_file):
        """Test error handling"""
        workflow = VideoGenerationWorkflow()
        
        # Create state with error
        state = VideoGenerationState()
        state.status = "FAILED"
        state.error_message = "Test error message"
        state.temp_files = [sample_audio_file]  # Add a temp file to clean up
        
        result_state = await workflow._handle_error(state)
        
        assert result_state.status == "FAILED"
        assert result_state.progress == 100
        assert result_state.error_message == "Test error message"
    
    @pytest.mark.asyncio
    async def test_run_workflow_success(self, sample_video_file):
        """Test complete workflow execution with mocked services"""
        # Create a new workflow with real service instances (but mocked methods)
        with patch('app.workflows.video_generation.TTSServiceManager') as mock_tts_cls, \
             patch('app.workflows.video_generation.VideoProcessingService') as mock_video_cls:
            
            mock_tts_service = Mock()
            mock_video_service = Mock()
            
            mock_tts_cls.return_value = mock_tts_service
            mock_video_cls.return_value = mock_video_service
            
            # Mock all the service methods
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_processed_audio:
                temp_processed_audio_path = temp_processed_audio.name
            
            try:
                mock_tts_service.generate_audio = AsyncMock(return_value=temp_audio_path)
                mock_video_service.validate_video_format = AsyncMock(return_value=True)
                mock_video_service.extract_video_duration = AsyncMock(return_value=120.0)
                mock_video_service.extract_audio_duration = AsyncMock(return_value=100.0)
                mock_video_service.adjust_audio_to_video_duration = AsyncMock(return_value=temp_processed_audio_path)
                mock_video_service.merge_audio_video = AsyncMock(return_value="/output/final_video.mp4")
                
                workflow = VideoGenerationWorkflow()
                
                input_data = {
                    "input_file_path": sample_video_file,
                    "description_text": "This is a beautiful property with great amenities.",
                    "target_language": "en"
                }
                
                result = await workflow.run_workflow(input_data)
                
                # Verify the workflow completed successfully
                assert result.status == "COMPLETED"
                assert result.progress == 100
                assert result.output_path == "/output/final_video.mp4"
                
                # Verify all steps were called
                mock_tts_service.generate_audio.assert_called_once()
                mock_video_service.merge_audio_video.assert_called_once()
                
            finally:
                # Clean up temp files
                for temp_path in [temp_audio_path, temp_processed_audio_path]:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_run_workflow_with_validation_error(self):
        """Test workflow execution with validation error"""
        with patch('app.workflows.video_generation.TTSServiceManager') as mock_tts_cls, \
             patch('app.workflows.video_generation.VideoProcessingService') as mock_video_cls:
            
            mock_tts_service = Mock()
            mock_video_service = Mock()
            
            mock_tts_cls.return_value = mock_tts_service
            mock_video_cls.return_value = mock_video_service
            
            # Mock format validation to fail
            mock_video_service.validate_video_format = AsyncMock(return_value=False)
            
            workflow = VideoGenerationWorkflow()
            
            input_data = {
                "input_file_path": "/invalid/format.avi",  # This will fail validation
                "description_text": "This is a beautiful property with great amenities.",
                "target_language": "en"
            }
            
            result = await workflow.run_workflow(input_data)
            
            # Verify the workflow failed at validation
            assert result.status == "FAILED"
            assert result.progress == 100
            assert result.error_message is not None
            assert "Unsupported video format" in result.error_message
    
    def test_route_next_logic(self):
        """Test the routing logic for next steps"""
        workflow = VideoGenerationWorkflow()
        
        # Test routing from different states
        state = VideoGenerationState()
        
        # Test routing from VALIDATING
        state.status = "VALIDATING"
        next_step = workflow._route_next(state)
        assert next_step == "process_text"
        
        # Test routing from TEXT_PROCESSING
        state.status = "TEXT_PROCESSING"
        next_step = workflow._route_next(state)
        assert next_step == "generate_audio"
        
        # Test routing from TTS_GENERATION
        state.status = "TTS_GENERATION"
        next_step = workflow._route_next(state)
        assert next_step == "process_audio"
        
        # Test routing from AUDIO_PROCESSING
        state.status = "AUDIO_PROCESSING"
        next_step = workflow._route_next(state)
        assert next_step == "merge_video"
        
        # Test routing from VIDEO_MERGING
        state.status = "VIDEO_MERGING"
        next_step = workflow._route_next(state)
        assert next_step == "completed"
        
        # Test routing from COMPLETED
        state.status = "COMPLETED"
        next_step = workflow._route_next(state)
        assert next_step == "completed"
        
        # Test routing from FAILED state
        state.status = "FAILED"
        next_step = workflow._route_next(state)
        assert next_step == "handle_error"


if __name__ == "__main__":
    pytest.main([__file__])