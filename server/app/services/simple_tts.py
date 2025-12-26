import os
import requests
import json
from app.config import settings
from typing import Optional
import tempfile
import subprocess

class SimpleTTSService:
    """
    Simple TTS service using Google Gemini for translation and system TTS
    """
    
    def __init__(self):
        self.api_key = settings.google_gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using Google Gemini"""
        if not self.api_key or self.api_key == "your_google_api_key_here":
            # If no API key, return original text
            return text
            
        if target_language == "en":
            return text
        
        language_names = {
            "te": "Telugu", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
            "ko": "Korean", "zh": "Chinese", "hi": "Hindi", "ar": "Arabic"
        }
        
        target_lang_name = language_names.get(target_language, target_language)
        
        prompt = f"Translate this text to {target_lang_name}. Return only the translation:\n\n{text}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1000}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            print(f"Translation failed: {response.status_code}")
            return text
            
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text
    
    def synthesize_speech(self, text: str, language_code: str, voice_name: str) -> bytes:
        """Generate speech using system TTS or OpenAI"""
        
        # First translate if needed
        if language_code != "en":
            translated_text = self.translate_text(text, language_code)
        else:
            translated_text = text
        
        print(f"Generating TTS for: {translated_text[:100]}...")
        
        # Try different TTS methods in order of preference
        
        # Method 1: Try Google TTS (gTTS) - requires internet
        try:
            return self._generate_gtts(translated_text, language_code)
        except Exception as e:
            print(f"Google TTS failed: {e}")
        
        # Method 2: Try OpenAI TTS if API key is available
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            try:
                return self._generate_openai_tts(translated_text)
            except Exception as e:
                print(f"OpenAI TTS failed: {e}")
        
        # Method 3: Try pyttsx3 (offline TTS)
        try:
            return self._generate_pyttsx3_tts(translated_text)
        except Exception as e:
            print(f"Pyttsx3 TTS failed: {e}")
        
        # Fallback: Create a longer silent audio with text info
        print("All TTS methods failed, creating extended silent audio")
        return self._create_text_based_audio(translated_text)
    
    def _generate_gtts(self, text: str, language_code: str = "en") -> bytes:
        """Generate TTS using Google Text-to-Speech"""
        from gtts import gTTS
        import io
        
        # Map language codes
        lang_map = {
            "en": "en",
            "te": "te", 
            "es": "es",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "pt": "pt",
            "ru": "ru",
            "ja": "ja",
            "ko": "ko",
            "zh": "zh",
            "hi": "hi",
            "ar": "ar"
        }
        
        lang = lang_map.get(language_code, "en")
        
        # Create gTTS object
        tts = gTTS(text=text[:1000], lang=lang, slow=False)  # Limit text length
        
        # Save to bytes
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Convert MP3 to WAV using ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            mp3_file.write(mp3_fp.read())
            mp3_path = mp3_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
        
        # Convert MP3 to WAV
        cmd = ['ffmpeg', '-y', '-i', mp3_path, '-acodec', 'pcm_s16le', '-ar', '44100', wav_path]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0 and os.path.exists(wav_path):
            with open(wav_path, 'rb') as f:
                audio_content = f.read()
            os.unlink(mp3_path)
            os.unlink(wav_path)
            return audio_content
        
        # Cleanup and raise error
        if os.path.exists(mp3_path):
            os.unlink(mp3_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        
        raise Exception(f"gTTS conversion failed: {result.stderr}")
    
    def _generate_pyttsx3_tts(self, text: str) -> bytes:
        """Generate TTS using pyttsx3 (offline)"""
        import pyttsx3
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            
            # Save to file
            engine.save_to_file(text[:500], temp_path)
            engine.runAndWait()
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, 'rb') as f:
                    audio_content = f.read()
                os.unlink(temp_path)
                return audio_content
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise Exception(f"Pyttsx3 failed: {str(e)}")
        
        raise Exception("Pyttsx3 produced no audio")
        """Generate TTS using OpenAI API"""
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text[:4000]  # OpenAI limit
        )
        
        return response.content
    
    def _generate_espeak_tts(self, text: str) -> bytes:
        """Generate TTS using espeak"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Use espeak to generate speech
        cmd = [
            'espeak', 
            '-w', temp_path,  # Write to WAV file
            '-s', '150',      # Speed (words per minute)
            '-p', '50',       # Pitch
            '-a', '100',      # Amplitude
            text[:500]        # Limit text length
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                audio_content = f.read()
            os.unlink(temp_path)
            return audio_content
        
        raise Exception(f"Espeak failed: {result.stderr}")
    
    def _generate_festival_tts(self, text: str) -> bytes:
        """Generate TTS using festival"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create festival script
        festival_script = f'(utt.save.wave (SayText "{text[:300]}") "{temp_path}" \'riff)'
        
        cmd = ['festival', '--batch', '--pipe']
        result = subprocess.run(cmd, input=festival_script, text=True, capture_output=True)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                audio_content = f.read()
            os.unlink(temp_path)
            return audio_content
        
        raise Exception(f"Festival failed: {result.stderr}")
    
    def _generate_pico_tts(self, text: str) -> bytes:
        """Generate TTS using pico2wave"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        cmd = ['pico2wave', '-w', temp_path, text[:300]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                audio_content = f.read()
            os.unlink(temp_path)
            return audio_content
        
        raise Exception(f"Pico2wave failed: {result.stderr}")
    
    def _create_text_based_audio(self, text: str) -> bytes:
        """Create audio with duration based on text length"""
        # Calculate duration based on text length (average reading speed)
        words = len(text.split())
        duration = max(5.0, words * 0.4)  # Minimum 5 seconds, ~150 words per minute
        
        print(f"Creating {duration:.1f} second audio for {words} words")
        
        return self._create_silent_wav(duration)
    
    def _create_silent_wav(self, duration: float) -> bytes:
        """Create a silent WAV file of specified duration"""
        import struct
        
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        
        # WAV header
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + num_samples * 2,  # File size
            b'WAVE',
            b'fmt ',
            16,  # PCM format chunk size
            1,   # PCM format
            1,   # Mono
            sample_rate,
            sample_rate * 2,  # Byte rate
            2,   # Block align
            16,  # Bits per sample
            b'data',
            num_samples * 2  # Data size
        )
        
        # Silent audio data (all zeros)
        audio_data = b'\x00\x00' * num_samples
        
        return header + audio_data


class TTSManager:
    """Updated TTS Manager using the simple TTS service"""
    
    def __init__(self):
        self.tts_service = SimpleTTSService()
    
    def synthesize_speech(self, text: str, target_language: str, voice_name: str = "default") -> bytes:
        """Generate speech audio"""
        return self.tts_service.synthesize_speech(text, target_language, voice_name)