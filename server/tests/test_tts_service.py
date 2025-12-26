import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from app.services.tts_service import (
    TTSServiceManager,
    OpenAITTSService,
    GoogleCloudTTSService,
    BaseTTSService
)
from app.config import settings


@pytest.fixture
def sample_text():
    return "This is a test property with beautiful amenities and great location."


@pytest.fixture
def temp_audio_file():
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


class TestBaseTTSService:
    def test_abstract_methods(self):
        """Test that BaseTTSService has abstract methods"""
        with pytest.raises(TypeError):
            BaseTTSService()


class TestOpenAITTSService:
    @pytest.mark.asyncio
    async def test_init_with_valid_api_key(self, monkeypatch):
        """Test OpenAI TTS service initialization with valid API key"""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_client.audio = Mock()
        mock_client.audio.speech = Mock()
        mock_client.audio.speech.create = AsyncMock()
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            with patch('app.services.tts_service.AsyncOpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                service = OpenAITTSService()
                assert service.client == mock_client
    
    @pytest.mark.asyncio
    async def test_generate_audio_success(self, sample_text, temp_audio_file):
        """Test successful audio generation with OpenAI TTS"""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.stream_to_file = Mock()
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            with patch('app.services.tts_service.AsyncOpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                service = OpenAITTSService()
                result = await service.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                # Verify the client was called correctly
                mock_client.audio.speech.create.assert_called_once_with(
                    model=settings.openai_tts_model,
                    voice=settings.openai_tts_voice,
                    input=sample_text
                )
                
                # Verify the response method was called
                mock_response.stream_to_file.assert_called_once_with(temp_audio_file)
                
                assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_different_languages(self, sample_text, temp_audio_file):
        """Test audio generation with different languages"""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.stream_to_file = Mock()
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_tts_voice = "nova"
            with patch('app.services.tts_service.AsyncOpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                service = OpenAITTSService()
                
                # Test English
                await service.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                # For English, it should use the default voice from settings
                mock_client.audio.speech.create.assert_called_with(
                    model=settings.openai_tts_model,
                    voice=settings.openai_tts_voice,
                    input=sample_text
                )
                
                # Reset mock and test Telugu
                mock_client.audio.speech.create.reset_mock()
                await service.generate_audio(
                    text=sample_text,
                    language_code="te",
                    output_path=temp_audio_file
                )
                
                # For Telugu, it should use "onyx" voice
                mock_client.audio.speech.create.assert_called_with(
                    model=settings.openai_tts_model,
                    voice="onyx",
                    input=sample_text
                )
    
    @pytest.mark.asyncio
    async def test_generate_audio_failure(self, sample_text, temp_audio_file):
        """Test audio generation failure handling"""
        # Mock the OpenAI client to raise an exception
        mock_client = Mock()
        mock_client.audio.speech.create = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            with patch('app.services.tts_service.AsyncOpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                service = OpenAITTSService()
                
                with pytest.raises(Exception, match="API Error"):
                    await service.generate_audio(
                        text=sample_text,
                        language_code="en",
                        output_path=temp_audio_file
                    )


class TestGoogleCloudTTSService:
    @pytest.mark.asyncio
    async def test_init_with_valid_config(self, monkeypatch):
        """Test Google Cloud TTS service initialization"""
        # Mock the Google Cloud TextToSpeech client
        mock_client = Mock()
        
        with patch('app.services.tts_service.texttospeech') as mock_tts:
            mock_tts.TextToSpeechClient.return_value = mock_client
            with patch('app.services.tts_service.settings') as mock_settings:
                mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
                
                service = GoogleCloudTTSService()
                assert service.client == mock_client
    
    @pytest.mark.asyncio
    async def test_generate_audio_success(self, sample_text, temp_audio_file):
        """Test successful audio generation with Google Cloud TTS"""
        # Mock the Google Cloud TextToSpeech client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.audio_content = b"fake audio content"
        mock_client.synthesize_speech = Mock(return_value=mock_response)
        
        with patch('app.services.tts_service.texttospeech') as mock_tts:
            mock_tts.TextToSpeechClient.return_value = mock_client
            mock_tts.VoiceSelectionParams = Mock(return_value="voice_params")
            mock_tts.AudioConfig = Mock(return_value="audio_config")
            mock_tts.AudioEncoding = Mock(MP3="MP3")
            
            with patch('app.services.tts_service.settings') as mock_settings:
                mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
                
                service = GoogleCloudTTSService()
                result = await service.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                # Verify the client was called correctly
                mock_client.synthesize_speech.assert_called_once()
                
                # Check that the output file was created
                assert os.path.exists(temp_audio_file)
                assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_different_languages(self, sample_text, temp_audio_file):
        """Test audio generation with different languages for Google Cloud TTS"""
        # Mock the Google Cloud TextToSpeech client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.audio_content = b"fake audio content"
        mock_client.synthesize_speech = Mock(return_value=mock_response)
        
        with patch('app.services.tts_service.texttospeech') as mock_tts:
            mock_tts.TextToSpeechClient.return_value = mock_client
            mock_tts.VoiceSelectionParams = Mock(return_value="voice_params")
            mock_tts.AudioConfig = Mock(return_value="audio_config")
            mock_tts.AudioEncoding = Mock(MP3="MP3")
            
            with patch('app.services.tts_service.settings') as mock_settings:
                mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
                
                service = GoogleCloudTTSService()
                
                # Test English
                await service.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                # Verify English parameters were used
                call_args = mock_client.synthesize_speech.call_args
                assert call_args is not None
                
                # Test Telugu
                await service.generate_audio(
                    text=sample_text,
                    language_code="te",
                    output_path=temp_audio_file
                )
                
                # Verify Telugu parameters were used
                call_args = mock_client.synthesize_speech.call_args
                assert call_args is not None


class TestTTSServiceManager:
    def test_init_without_api_keys(self):
        """Test TTS service manager initialization without API keys"""
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.google_cloud_credentials_path = None
            
            manager = TTSServiceManager()
            assert manager.openai_service is None
            assert manager.google_service is None
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_fallback(self, sample_text, temp_audio_file):
        """Test TTS service manager with OpenAI service"""
        # Mock OpenAI service
        mock_openai_service = AsyncMock()
        mock_openai_service.generate_audio = AsyncMock(return_value=temp_audio_file)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.google_cloud_credentials_path = None
            
            with patch('app.services.tts_service.OpenAITTSService') as mock_openai_class:
                mock_openai_class.return_value = mock_openai_service
                
                manager = TTSServiceManager()
                result = await manager.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                mock_openai_service.generate_audio.assert_called_once_with(
                    sample_text, "en", temp_audio_file
                )
                assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_google_fallback(self, sample_text, temp_audio_file):
        """Test TTS service manager with Google Cloud fallback"""
        # Mock Google Cloud service
        mock_google_service = AsyncMock()
        mock_google_service.generate_audio = AsyncMock(return_value=temp_audio_file)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
            
            with patch('app.services.tts_service.GoogleCloudTTSService') as mock_google_class:
                mock_google_class.return_value = mock_google_service
                
                manager = TTSServiceManager()
                result = await manager.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                mock_google_service.generate_audio.assert_called_once_with(
                    sample_text, "en", temp_audio_file
                )
                assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_both_services(self, sample_text, temp_audio_file):
        """Test TTS service manager with both services (OpenAI preferred)"""
        # Mock both services
        mock_openai_service = AsyncMock()
        mock_openai_service.generate_audio = AsyncMock(return_value=temp_audio_file)
        mock_google_service = AsyncMock()
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
            
            with patch('app.services.tts_service.OpenAITTSService') as mock_openai_class:
                mock_openai_class.return_value = mock_openai_service
                with patch('app.services.tts_service.GoogleCloudTTSService') as mock_google_class:
                    mock_google_class.return_value = mock_google_service
                    
                    manager = TTSServiceManager()
                    result = await manager.generate_audio(
                        text=sample_text,
                        language_code="en",
                        output_path=temp_audio_file
                    )
                    
                    # OpenAI should be called, not Google
                    mock_openai_service.generate_audio.assert_called_once_with(
                        sample_text, "en", temp_audio_file
                    )
                    mock_google_service.generate_audio.assert_not_called()
                    assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_with_fallback_on_error(self, sample_text, temp_audio_file):
        """Test TTS service manager fallback when primary service fails"""
        # Mock services with OpenAI failing and Google succeeding
        mock_openai_service = AsyncMock()
        mock_openai_service.generate_audio = AsyncMock(side_effect=Exception("OpenAI Error"))
        mock_google_service = AsyncMock()
        mock_google_service.generate_audio = AsyncMock(return_value=temp_audio_file)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
            
            with patch('app.services.tts_service.OpenAITTSService') as mock_openai_class:
                mock_openai_class.return_value = mock_openai_service
                with patch('app.services.tts_service.GoogleCloudTTSService') as mock_google_class:
                    mock_google_class.return_value = mock_google_service
                    
                    manager = TTSServiceManager()
                    result = await manager.generate_audio(
                        text=sample_text,
                        language_code="en",
                        output_path=temp_audio_file
                    )
                    
                    # OpenAI should be called first and fail
                    mock_openai_service.generate_audio.assert_called_once_with(
                        sample_text, "en", temp_audio_file
                    )
                    # Google should be called as fallback
                    mock_google_service.generate_audio.assert_called_once_with(
                        sample_text, "en", temp_audio_file
                    )
                    assert result == temp_audio_file
    
    @pytest.mark.asyncio
    async def test_generate_audio_all_services_fail(self, sample_text, temp_audio_file):
        """Test TTS service manager when all services fail"""
        # Mock both services to fail
        mock_openai_service = AsyncMock()
        mock_openai_service.generate_audio = AsyncMock(side_effect=Exception("OpenAI Error"))
        mock_google_service = AsyncMock()
        mock_google_service.generate_audio = AsyncMock(side_effect=Exception("Google Error"))
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.google_cloud_credentials_path = "/path/to/creds.json"
            
            with patch('app.services.tts_service.OpenAITTSService') as mock_openai_class:
                mock_openai_class.return_value = mock_openai_service
                with patch('app.services.tts_service.GoogleCloudTTSService') as mock_google_class:
                    mock_google_class.return_value = mock_google_service
                    
                    manager = TTSServiceManager()
                    
                    with pytest.raises(Exception, match="All TTS services failed"):
                        await manager.generate_audio(
                            text=sample_text,
                            language_code="en",
                            output_path=temp_audio_file
                        )
    
    @pytest.mark.asyncio
    async def test_audio_caching(self, sample_text, temp_audio_file):
        """Test audio caching functionality"""
        # Mock OpenAI service
        mock_openai_service = AsyncMock()
        mock_openai_service.generate_audio = AsyncMock(return_value=temp_audio_file)
        
        with patch('app.services.tts_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.google_cloud_credentials_path = None
            
            with patch('app.services.tts_service.OpenAITTSService') as mock_openai_class:
                mock_openai_class.return_value = mock_openai_service
                
                manager = TTSServiceManager()
                
                # First call - should generate audio
                result1 = await manager.generate_audio(
                    text=sample_text,
                    language_code="en",
                    output_path=temp_audio_file
                )
                
                # Second call with same text - should use cache
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file2:
                    temp_file2_path = temp_file2.name
                
                try:
                    result2 = await manager.generate_audio(
                        text=sample_text,  # Same text
                        language_code="en",
                        output_path=temp_file2_path
                    )
                    
                    # OpenAI should only be called once (for the first request)
                    assert mock_openai_service.generate_audio.call_count == 1
                    assert result1 == result2
                finally:
                    if os.path.exists(temp_file2_path):
                        os.remove(temp_file2_path)


if __name__ == "__main__":
    pytest.main([__file__])