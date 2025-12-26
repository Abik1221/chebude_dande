import asyncio
from typing import Dict, Any, Optional
from langchain_core.runnables import ConfigurableFieldSpec
from langgraph.graph import StateGraph, END
from app.services.tts_service import TTSServiceManager
from app.services.video_service import VideoProcessingService
from app.config import settings
from loguru import logger
import tempfile
import os


# Define the state structure
class VideoGenerationState:
    def __init__(self):
        self.input_data = {}
        self.status = "PENDING"
        self.progress = 0
        self.error_message = None
        self.temp_files = []
        self.output_path = None


class VideoGenerationWorkflow:
    def __init__(self):
        self.tts_service = TTSServiceManager()
        self.video_service = VideoProcessingService()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self):
        # Create a state graph
        workflow = StateGraph(VideoGenerationState)
        
        # Add nodes to the workflow
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("process_text", self._process_text)
        workflow.add_node("generate_audio", self._generate_audio)
        workflow.add_node("process_audio", self._process_audio)
        workflow.add_node("merge_video", self._merge_video)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set the entry point
        workflow.set_entry_point("validate_input")
        
        # Define conditional edges from each node
        workflow.add_conditional_edges(
            "validate_input",
            self._route_next,
            {
                "process_text": "process_text",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "process_text",
            self._route_next,
            {
                "generate_audio": "generate_audio",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_audio",
            self._route_next,
            {
                "process_audio": "process_audio",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "process_audio",
            self._route_next,
            {
                "merge_video": "merge_video",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "merge_video",
            self._route_next,
            {
                "completed": END,
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _validate_input(self, state: VideoGenerationState):
        """
        Validate input parameters
        """
        logger.info("Validating input parameters")
        state.status = "VALIDATING"
        state.progress = 5
        
        try:
            input_data = state.input_data
            
            # Validate required fields
            required_fields = ["input_file_path", "description_text", "target_language"]
            for field in required_fields:
                if field not in input_data or not input_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate video file exists
            video_path = input_data["input_file_path"]
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file does not exist: {video_path}")
            
            # Validate video format
            is_valid_format = await self.video_service.validate_video_format(video_path)
            if not is_valid_format:
                raise ValueError(f"Unsupported video format. Supported formats: {settings.allowed_video_formats}")
            
            # Validate description text length
            description = input_data["description_text"]
            if len(description) > settings.max_description_length:
                raise ValueError(f"Description text too long. Maximum length: {settings.max_description_length}")
            
            # Validate target language exists
            target_language = input_data["target_language"]
            # In a real implementation, you would check against the database
            if target_language not in ["en", "te"]:  # For now, just check basic languages
                raise ValueError(f"Unsupported language: {target_language}")
            
            logger.info("Input validation completed successfully")
            state.status = "TEXT_PROCESSING"
            state.progress = 10
            
            return state
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            state.status = "FAILED"
            state.error_message = str(e)
            state.progress = 100
            return state
    
    async def _process_text(self, state: VideoGenerationState):
        """
        Process and clean text for TTS
        """
        logger.info("Processing text for TTS")
        state.status = "TEXT_PROCESSING"
        state.progress = 20
        
        try:
            # In a real implementation, you might clean and process the text here
            # For now, we'll just pass through
            input_data = state.input_data
            description = input_data["description_text"]
            
            # Clean text (remove extra whitespace, etc.)
            cleaned_description = " ".join(description.split())
            input_data["cleaned_description"] = cleaned_description
            
            logger.info("Text processing completed")
            state.status = "TTS_GENERATION"
            state.progress = 30
            
            return state
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            state.status = "FAILED"
            state.error_message = str(e)
            state.progress = 100
            return state
    
    async def _generate_audio(self, state: VideoGenerationState):
        """
        Generate audio from text using TTS service
        """
        logger.info("Generating audio with TTS service")
        state.status = "TTS_GENERATION"
        state.progress = 40
        
        try:
            input_data = state.input_data
            
            # Create temporary file for audio
            temp_audio_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.mp3',
                dir=settings.temp_folder
            )
            temp_audio_file.close()
            state.temp_files.append(temp_audio_file.name)
            
            # Generate audio using TTS service
            await self.tts_service.generate_audio(
                text=input_data["cleaned_description"],
                language_code=input_data["target_language"],
                output_path=temp_audio_file.name
            )
            
            input_data["audio_file_path"] = temp_audio_file.name
            
            logger.info("Audio generation completed")
            state.status = "AUDIO_PROCESSING"
            state.progress = 60
            
            return state
            
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            state.status = "FAILED"
            state.error_message = str(e)
            state.progress = 100
            return state
    
    async def _process_audio(self, state: VideoGenerationState):
        """
        Process audio for video merging
        """
        logger.info("Processing audio for video merging")
        state.status = "AUDIO_PROCESSING"
        state.progress = 70
        
        try:
            input_data = state.input_data
            video_path = input_data["input_file_path"]
            audio_path = input_data["audio_file_path"]
            
            # Create temporary file for processed audio
            temp_processed_audio = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.mp3',
                dir=settings.temp_folder
            )
            temp_processed_audio.close()
            state.temp_files.append(temp_processed_audio.name)
            
            # Adjust audio duration to match video
            await self.video_service.adjust_audio_to_video_duration(
                audio_path=audio_path,
                video_path=video_path,
                output_path=temp_processed_audio.name
            )
            
            input_data["processed_audio_path"] = temp_processed_audio.name
            
            logger.info("Audio processing completed")
            state.status = "VIDEO_MERGING"
            state.progress = 80
            
            return state
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            state.status = "FAILED"
            state.error_message = str(e)
            state.progress = 100
            return state
    
    async def _merge_video(self, state: VideoGenerationState):
        """
        Merge audio with video using FFmpeg
        """
        logger.info("Merging audio with video")
        state.status = "VIDEO_MERGING"
        state.progress = 90
        
        try:
            input_data = state.input_data
            video_path = input_data["input_file_path"]
            audio_path = input_data["processed_audio_path"]
            
            # Generate output path
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(
                settings.output_folder, 
                f"{video_name}_narrated.mp4"
            )
            
            # Ensure output directory exists
            os.makedirs(settings.output_folder, exist_ok=True)
            
            # Merge audio and video
            await self.video_service.merge_audio_video(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path
            )
            
            state.output_path = output_path
            state.status = "COMPLETED"
            state.progress = 100
            
            logger.info(f"Video merging completed: {output_path}")
            
            return state
            
        except Exception as e:
            logger.error(f"Video merging error: {e}")
            state.status = "FAILED"
            state.error_message = str(e)
            state.progress = 100
            return state
    
    async def _handle_error(self, state: VideoGenerationState):
        """
        Handle errors in the workflow
        """
        logger.error(f"Workflow failed with error: {state.error_message}")
        state.status = "FAILED"
        state.progress = 100
        
        # Clean up temp files
        for temp_file in state.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up temp file {temp_file}: {e}")
        
        return state
    
    def _route_next(self, state: VideoGenerationState) -> str:
        """
        Determine the next node based on current state
        """
        if state.status == "FAILED":
            return "handle_error"
        
        # Route based on current status
        routing_map = {
            "VALIDATING": "process_text",
            "TEXT_PROCESSING": "generate_audio",
            "TTS_GENERATION": "process_audio",
            "AUDIO_PROCESSING": "merge_video",
            "VIDEO_MERGING": "completed",
            "COMPLETED": "completed"
        }
        
        next_step = routing_map.get(state.status, "handle_error")
        if next_step == "completed":
            return "completed"
        return next_step
    
    async def run_workflow(self, input_data: Dict[str, Any]) -> VideoGenerationState:
        """
        Run the video generation workflow
        """
        # Initialize state
        state = VideoGenerationState()
        state.input_data = input_data
        
        # Ensure required directories exist
        os.makedirs(settings.temp_folder, exist_ok=True)
        os.makedirs(settings.output_folder, exist_ok=True)
        os.makedirs(settings.upload_folder, exist_ok=True)
        
        # Run the workflow
        result = await self.workflow.ainvoke(state)
        
        return result