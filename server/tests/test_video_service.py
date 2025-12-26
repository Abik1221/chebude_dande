import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from app.services.video_service import VideoProcessingService
from app.config import settings


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
def temp_output_file():
    """Create a temporary output file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


class TestVideoProcessingService:
    def test_init_success(self):
        """Test successful initialization of VideoProcessingService"""
        # This test requires FFmpeg to be installed, so we'll mock the check
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            assert service is not None
    
    def test_init_without_ffmpeg(self):
        """Test initialization fails when FFmpeg is not available"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=False):
            with pytest.raises(RuntimeError, match="FFmpeg is not installed or not available in PATH"):
                VideoProcessingService()
    
    def test_check_ffmpeg_success(self):
        """Test FFmpeg check when FFmpeg is available"""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            service = Mock()  # Mock service for this test
            result = VideoProcessingService._check_ffmpeg(service)
            
            mock_run.assert_called_once_with(['ffmpeg', '-version'], stdout=-3, stderr=-3)
            assert result is True
    
    def test_check_ffmpeg_failure(self):
        """Test FFmpeg check when FFmpeg is not available"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            service = Mock()  # Mock service for this test
            result = VideoProcessingService._check_ffmpeg(service)
            
            assert result is False


class TestMergeAudioVideo:
    @pytest.mark.asyncio
    async def test_merge_audio_video_success(self, sample_video_file, sample_audio_file, temp_output_file):
        """Test successful merging of audio and video"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess creation
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b'stdout', b'stderr'))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                result = await service.merge_audio_video(
                    video_path=sample_video_file,
                    audio_path=sample_audio_file,
                    output_path=temp_output_file
                )
                
                # Verify subprocess was called with correct arguments
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                
                # Check that the command contains the expected elements
                assert 'ffmpeg' in args
                assert sample_video_file in args
                assert sample_audio_file in args
                assert temp_output_file in args
                
                # Verify the result
                assert result == temp_output_file
                assert os.path.exists(temp_output_file)
    
    @pytest.mark.asyncio
    async def test_merge_audio_video_ffmpeg_error(self, sample_video_file, sample_audio_file, temp_output_file):
        """Test merging fails when FFmpeg returns error"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return error
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b'stdout', b'ffmpeg error'))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="FFmpeg failed with error: ffmpeg error"):
                    await service.merge_audio_video(
                        video_path=sample_video_file,
                        audio_path=sample_audio_file,
                        output_path=temp_output_file
                    )
    
    @pytest.mark.asyncio
    async def test_merge_audio_video_exception(self, sample_video_file, sample_audio_file, temp_output_file):
        """Test merging handles exceptions properly"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess creation to raise an exception
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.side_effect = Exception("Subprocess error")
                
                with pytest.raises(Exception, match="Subprocess error"):
                    await service.merge_audio_video(
                        video_path=sample_video_file,
                        audio_path=sample_audio_file,
                        output_path=temp_output_file
                    )


class TestExtractDurations:
    @pytest.mark.asyncio
    async def test_extract_audio_duration_success(self, sample_audio_file):
        """Test successful extraction of audio duration"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return a duration
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b'123.45', b''))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                duration = await service.extract_audio_duration(sample_audio_file)
                
                # Verify subprocess was called with correct arguments
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                
                # Check that the command contains the expected elements
                assert 'ffprobe' in args
                assert sample_audio_file in args
                
                # Verify the result
                assert duration == 123.45
    
    @pytest.mark.asyncio
    async def test_extract_audio_duration_ffprobe_error(self, sample_audio_file):
        """Test audio duration extraction fails when ffprobe returns error"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return error
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b'', b'ffprobe error'))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="ffprobe failed with error: ffprobe error"):
                    await service.extract_audio_duration(sample_audio_file)
    
    @pytest.mark.asyncio
    async def test_extract_video_duration_success(self, sample_video_file):
        """Test successful extraction of video duration"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return a duration
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b'98.76', b''))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                duration = await service.extract_video_duration(sample_video_file)
                
                # Verify subprocess was called with correct arguments
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                
                # Check that the command contains the expected elements
                assert 'ffprobe' in args
                assert sample_video_file in args
                
                # Verify the result
                assert duration == 98.76
    
    @pytest.mark.asyncio
    async def test_extract_video_duration_ffprobe_error(self, sample_video_file):
        """Test video duration extraction fails when ffprobe returns error"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return error
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b'', b'ffprobe error'))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="ffprobe failed with error: ffprobe error"):
                    await service.extract_video_duration(sample_video_file)


class TestAdjustAudioDuration:
    @pytest.mark.asyncio
    async def test_adjust_audio_to_video_duration_success(self, sample_audio_file, sample_video_file):
        """Test successful adjustment of audio to match video duration"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock duration extraction
            with patch.object(service, 'extract_video_duration', return_value=100.0):
                with patch.object(service, 'extract_audio_duration', return_value=80.0):
                    # Mock the subprocess for audio adjustment
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b'stdout', b'stderr'))
                    
                    with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                        mock_create.return_value = mock_process
                        
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_output:
                            temp_output_path = temp_output.name
                        
                        try:
                            result = await service.adjust_audio_to_video_duration(
                                audio_path=sample_audio_file,
                                video_path=sample_video_file,
                                output_path=temp_output_path
                            )
                            
                            # Verify subprocess was called (for padding)
                            mock_create.assert_called_once()
                            args, kwargs = mock_create.call_args
                            
                            # Check that the command contains audio adjustment parameters
                            assert 'ffmpeg' in args
                            assert sample_audio_file in args
                            assert 'apad=pad_dur=20.0' in str(args)  # 100.0 - 80.0 = 20.0
                            
                            assert result == temp_output_path
                            assert os.path.exists(temp_output_path)
                        finally:
                            if os.path.exists(temp_output_path):
                                os.remove(temp_output_path)
    
    @pytest.mark.asyncio
    async def test_adjust_audio_trim_to_video(self, sample_audio_file, sample_video_file):
        """Test trimming audio when it's longer than video"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock duration extraction - audio longer than video
            with patch.object(service, 'extract_video_duration', return_value=80.0):
                with patch.object(service, 'extract_audio_duration', return_value=100.0):
                    # Mock the subprocess for audio trimming
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b'stdout', b'stderr'))
                    
                    with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                        mock_create.return_value = mock_process
                        
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_output:
                            temp_output_path = temp_output.name
                        
                        try:
                            result = await service.adjust_audio_to_video_duration(
                                audio_path=sample_audio_file,
                                video_path=sample_video_file,
                                output_path=temp_output_path
                            )
                            
                            # Verify subprocess was called (for trimming)
                            mock_create.assert_called_once()
                            args, kwargs = mock_create.call_args
                            
                            # Check that the command contains trim parameter
                            assert 'ffmpeg' in args
                            assert sample_audio_file in args
                            assert '-t' in args  # Should have trim parameter
                            assert '80.0' in args  # Should be trimmed to video duration
                            
                            assert result == temp_output_path
                        finally:
                            if os.path.exists(temp_output_path):
                                os.remove(temp_output_path)
    
    @pytest.mark.asyncio
    async def test_adjust_audio_similar_durations(self, sample_audio_file, sample_video_file):
        """Test when audio and video durations are similar (no adjustment needed)"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock duration extraction - similar durations
            with patch.object(service, 'extract_video_duration', return_value=100.0):
                with patch.object(service, 'extract_audio_duration', return_value=100.05):  # Very close
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_output:
                        temp_output_path = temp_output.name
                    
                    try:
                        result = await service.adjust_audio_to_video_duration(
                            audio_path=sample_audio_file,
                            video_path=sample_video_file,
                            output_path=temp_output_path
                        )
                        
                        # Should just copy the file without calling ffmpeg
                        # (This would require checking if shutil.copy2 was called, but for now
                        # we'll just verify the output file exists)
                        assert result == temp_output_path
                        assert os.path.exists(temp_output_path)
                    finally:
                        if os.path.exists(temp_output_path):
                            os.remove(temp_output_path)


class TestVideoValidation:
    @pytest.mark.asyncio
    async def test_validate_video_format_supported(self, sample_video_file):
        """Test validation of supported video formats"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Test with supported format
            result = await service.validate_video_format(sample_video_file)
            assert result is True  # Since our temp file has .mp4 extension
    
    @pytest.mark.asyncio
    async def test_validate_video_format_unsupported(self):
        """Test validation of unsupported video formats"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Create a temp file with unsupported extension
            with tempfile.NamedTemporaryFile(suffix='.unsupported', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                result = await service.validate_video_format(temp_file_path)
                assert result is False
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_validate_video_format_exception(self):
        """Test validation handles exceptions properly"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Test with non-existent file path
            result = await service.validate_video_format("/non/existent/file.mp4")
            assert result is False  # Should return False for invalid path


class TestGetVideoInfo:
    @pytest.mark.asyncio
    async def test_get_video_info_success(self, sample_video_file):
        """Test successful retrieval of video information"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return video info
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b'{"format": {"duration": "123.45"}}', b''))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                info = await service.get_video_info(sample_video_file)
                
                # Verify subprocess was called with correct arguments
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                
                # Check that the command contains the expected elements
                assert 'ffprobe' in args
                assert sample_video_file in args
                assert 'json' in args  # Should request JSON format
                
                # Verify the result
                assert info == {"format": {"duration": "123.45"}}
    
    @pytest.mark.asyncio
    async def test_get_video_info_ffprobe_error(self, sample_video_file):
        """Test video info retrieval fails when ffprobe returns error"""
        with patch('app.services.video_service.VideoProcessingService._check_ffmpeg', return_value=True):
            service = VideoProcessingService()
            
            # Mock the subprocess to return error
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b'', b'ffprobe error'))
            
            with patch('app.services.video_service.asyncio.create_subprocess_exec') as mock_create:
                mock_create.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="ffprobe failed with error: ffprobe error"):
                    await service.get_video_info(sample_video_file)


if __name__ == "__main__":
    pytest.main([__file__])