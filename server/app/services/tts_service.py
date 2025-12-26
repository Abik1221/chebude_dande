import os
import asyncio
import tempfile
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from loguru import logger
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class BaseTTSService(ABC):
    """
    Abstract base class for TTS services
    """
    
    @abstractmethod
    async def generate_audio(self, text: str, language_code: str, output_path: str) -> str:
        """
        Generate audio from text
        :param text: Input text to convert to speech
        :param language_code: Target language code (e.g., 'en', 'te')
        :param output_path: Path to save the generated audio file
        :return: Path to the generated audio file
        """
        pass


class OpenAITTSService(BaseTTSService):
    """
    OpenAI TTS service implementation
    """
    
    def __init__(self):
        # Import here to avoid issues if OpenAI is not installed
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            logger.error("OpenAI library not installed. Please install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_audio(self, text: str, language_code: str, output_path: str) -> str:
        """
        Generate audio using OpenAI TTS API
        """
        try:
            # Map language codes to appropriate voices
            language_to_voice = {
                "en": settings.openai_tts_voice or "nova",  # Default to nova for English
                "te": "onyx",  # Using onyx for Telugu as it works well for multiple languages
            }
            
            voice = language_to_voice.get(language_code, "nova")
            
            logger.info(f"Generating audio with OpenAI TTS for language: {language_code}, voice: {voice}")
            
            # Generate speech using OpenAI
            response = await self.client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=voice,
                input=text
            )
            
            # Save the audio file
            response.stream_to_file(output_path)
            
            logger.info(f"Audio successfully generated at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating audio with OpenAI: {e}")
            raise


class GoogleCloudTTSService(BaseTTSService):
    """
    Google Cloud TTS service implementation (fallback)
    """
    
    def __init__(self):
        # Import here to avoid issues if Google Cloud library is not installed
        try:
            from google.cloud import texttospeech
            if settings.google_cloud_credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_cloud_credentials_path
            self.client = texttospeech.TextToSpeechClient()
        except ImportError:
            logger.error("Google Cloud TextToSpeech library not installed. Please install with: pip install google-cloud-texttospeech")
            raise
        except Exception as e:
            logger.error(f"Error initializing Google Cloud TTS client: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_audio(self, text: str, language_code: str, output_path: str) -> str:
        """
        Generate audio using Google Cloud TTS API
        """
        try:
            # Map language codes to Google Cloud TTS voices
            language_to_voice = {
                "en": {"language_code": "en-US", "name": "en-US-Neural2-J"},
                "te": {"language_code": "te-IN", "name": "te-IN-Standard-A"},
            }
            
            lang_config = language_to_voice.get(language_code, {"language_code": "en-US", "name": "en-US-Neural2-J"})
            
            # Set the text input to be synthesized
            synthesis_input = {"text": text}
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=lang_config["language_code"],
                name=lang_config["name"]
            )
            
            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            logger.info(f"Generating audio with Google Cloud TTS for language: {language_code}")
            
            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            logger.info(f"Audio successfully generated at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating audio with Google Cloud TTS: {e}")
            raise


class TTSServiceManager:
    """
    TTS Service manager that handles multiple TTS providers with fallback
    """
    
    def __init__(self):
        self.openai_service = None
        self.google_service = None
        
        # Initialize services if API keys are available
        if settings.openai_api_key:
            try:
                self.openai_service = OpenAITTSService()
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI TTS service: {e}")
        
        if settings.google_cloud_credentials_path:
            try:
                self.google_service = GoogleCloudTTSService()
            except Exception as e:
                logger.warning(f"Could not initialize Google Cloud TTS service: {e}")
        
        # Create cache for repeated text generations (TTL: 1 hour)
        self.audio_cache = TTLCache(maxsize=100, ttl=3600)
    
    async def generate_audio(self, text: str, language_code: str, output_path: str) -> str:
        """
        Generate audio using available TTS services with fallback
        """
        # Check cache first
        cache_key = f"{text[:50]}_{language_code}"  # Use first 50 chars of text + language as cache key
        if cache_key in self.audio_cache:
            cached_path = self.audio_cache[cache_key]
            if os.path.exists(cached_path):
                logger.info(f"Using cached audio for text: {text[:50]}...")
                # Copy cached file to output path
                import shutil
                shutil.copy2(cached_path, output_path)
                return output_path
        
        # Try OpenAI first
        if self.openai_service:
            try:
                result = await self.openai_service.generate_audio(text, language_code, output_path)
                # Cache the result
                self.audio_cache[cache_key] = result
                return result
            except Exception as e:
                logger.warning(f"OpenAI TTS failed: {e}. Trying fallback service...")
        
        # Try Google Cloud TTS as fallback
        if self.google_service:
            try:
                result = await self.google_service.generate_audio(text, language_code, output_path)
                # Cache the result
                self.audio_cache[cache_key] = result
                return result
            except Exception as e:
                logger.error(f"Google Cloud TTS also failed: {e}")
        
        # If both services failed, raise an exception
        raise Exception("All TTS services failed. Please check your API keys and configurations.")