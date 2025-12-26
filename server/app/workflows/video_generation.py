from typing import TypedDict, Annotated, List
import functools
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from app.services.tts_service import TTSManager
from app.services.video_service import VideoProcessor
from app.models.job import Job
from sqlalchemy.orm import Session
import os
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoGenerationState(TypedDict):
    """State for the video generation workflow"""
    input_video_path: str
    description_text: str
    target_language: str
    processed_text: str  # Text after translation
    audio_path: str
    output_video_path: str
    job_id: int
    db_session: Session
    tts_manager: TTSManager
    video_processor: VideoProcessor
    error_message: str
    progress: int


def validate_inputs(state: VideoGenerationState) -> VideoGenerationState:
    """Validate input parameters"""
    logger.info("Validating inputs...")
    db = state['db_session']
    
    # Update job status
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        job.status = "VALIDATING"
        job.progress = 5
        db.commit()
    
    # Validate input video exists
    if not os.path.exists(state['input_video_path']):
        return {
            **state,
            "error_message": "Input video file does not exist",
            "progress": 5
        }
    
    # Validate description text
    if not state['description_text'] or len(state['description_text'].strip()) == 0:
        return {
            **state,
            "error_message": "Description text is required",
            "progress": 5
        }
    
    # Validate target language
    if not state['target_language']:
        return {
            **state,
            "error_message": "Target language is required",
            "progress": 5
        }
    
    logger.info("Inputs validated successfully")
    return {**state, "progress": 10}


def process_text(state: VideoGenerationState) -> VideoGenerationState:
    """Process text using translation service if needed"""
    logger.info("Processing text...")
    db = state['db_session']
    
    # Update job status
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        job.status = "PROCESSING_TEXT"
        job.progress = 15
        db.commit()
    
    try:
        # If target language is not English, translate the text using Gemini
        if state['target_language'] != 'en':
            logger.info(f"Translating text to {state['target_language']} using Gemini...")
            tts_manager = state['tts_manager']
            translated_text = tts_manager.translation_service.translate_text(
                state['description_text'], 
                state['target_language']
            )
            processed_text = translated_text
            logger.info("Text translation completed successfully")
        else:
            # If target language is English, use the original text
            processed_text = state['description_text']
            logger.info("Using original text (English target language)")
        
        return {
            **state,
            "processed_text": processed_text,
            "progress": 25
        }
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return {
            **state,
            "error_message": f"Text processing failed: {str(e)}",
            "progress": 25
        }


def generate_audio(state: VideoGenerationState) -> VideoGenerationState:
    """Generate audio using TTS service"""
    logger.info("Generating audio...")
    db = state['db_session']
    
    # Update job status
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        job.status = "GENERATING_AUDIO"
        job.progress = 35
        db.commit()
    
    try:
        # Get the processed text (original or translated)
        text_to_speak = state.get('processed_text', state['description_text'])
        
        # Generate audio using TTS
        tts_manager = state['tts_manager']
        
        # Determine voice based on language
        voice_mapping = {
            'en': 'en-US-Standard-C',
            'te': 'te-IN-Standard-A',
            'es': 'es-ES-Standard-A',
            'fr': 'fr-FR-Standard-A',
            'de': 'de-DE-Standard-A',
            'it': 'it-IT-Standard-A',
            'pt': 'pt-PT-Standard-A',
            'ru': 'ru-RU-Standard-A',
            'ja': 'ja-JP-Standard-A',
            'ko': 'ko-KR-Standard-A',
            'zh': 'cmn-CN-Standard-A',
            'hi': 'hi-IN-Standard-A',
            'ar': 'ar-XA-Standard-A',
        }
        
        voice_name = voice_mapping.get(state['target_language'], 'en-US-Standard-C')
        
        audio_content = tts_manager.synthesize_speech(
            text_to_speak,
            state['target_language'],
            voice_name
        )
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_file:
            audio_file.write(audio_content)
            audio_path = audio_file.name
        
        logger.info("Audio generation completed successfully")
        return {
            **state,
            "audio_path": audio_path,
            "progress": 55
        }
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        return {
            **state,
            "error_message": f"Audio generation failed: {str(e)}",
            "progress": 55
        }


def process_audio(state: VideoGenerationState) -> VideoGenerationState:
    """Process audio to match video duration"""
    logger.info("Processing audio...")
    db = state['db_session']
    
    # Update job status
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        job.status = "PROCESSING_AUDIO"
        job.progress = 65
        db.commit()
    
    try:
        video_processor = state['video_processor']
        
        # Get video duration
        video_duration = video_processor.get_video_duration(state['input_video_path'])
        
        # Adjust audio duration to match video
        adjusted_audio_path = video_processor.adjust_audio_duration(
            state['audio_path'],
            video_duration
        )
        
        logger.info("Audio processing completed successfully")
        return {
            **state,
            "audio_path": adjusted_audio_path,
            "progress": 75
        }
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return {
            **state,
            "error_message": f"Audio processing failed: {str(e)}",
            "progress": 75
        }


def merge_video_audio(state: VideoGenerationState) -> VideoGenerationState:
    """Merge audio and video files"""
    logger.info("Merging video and audio...")
    db = state['db_session']
    
    # Update job status
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        job.status = "MERGING_VIDEO"
        job.progress = 85
        db.commit()
    
    try:
        video_processor = state['video_processor']
        
        # Merge video and audio
        output_path = video_processor.merge_audio_video(
            state['input_video_path'],
            state['audio_path']
        )
        
        logger.info("Video and audio merging completed successfully")
        return {
            **state,
            "output_video_path": output_path,
            "progress": 95
        }
    except Exception as e:
        logger.error(f"Error merging video and audio: {str(e)}")
        return {
            **state,
            "error_message": f"Video and audio merging failed: {str(e)}",
            "progress": 95
        }


def update_job_status(state: VideoGenerationState) -> VideoGenerationState:
    """Update job status based on workflow result"""
    logger.info("Updating job status...")
    db = state['db_session']
    
    job = db.query(Job).filter(Job.id == state['job_id']).first()
    if job:
        if state.get('error_message'):
            job.status = "FAILED"
            job.error_message = state['error_message']
        else:
            job.status = "COMPLETED"
            job.output_file_path = state['output_video_path']
        
        job.progress = state['progress']
        db.commit()
    
    # Clean up temporary files
    try:
        if state.get('audio_path') and os.path.exists(state['audio_path']):
            os.remove(state['audio_path'])
    except Exception as e:
        logger.warning(f"Could not clean up audio file: {str(e)}")
    
    return state


def should_continue(state: VideoGenerationState) -> str:
    """Determine whether to continue or stop the workflow"""
    if state.get('error_message'):
        return "update_job_status"
    return "continue"


# Create the workflow graph
def create_video_generation_workflow():
    """Create and return the video generation workflow"""
    workflow = StateGraph(VideoGenerationState)
    
    # Add nodes
    workflow.add_node("validate_inputs", validate_inputs)
    workflow.add_node("process_text", process_text)
    workflow.add_node("generate_audio", generate_audio)
    workflow.add_node("process_audio", process_audio)
    workflow.add_node("merge_video_audio", merge_video_audio)
    workflow.add_node("update_job_status", update_job_status)
    
    # Set entry point
    workflow.set_entry_point("validate_inputs")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_inputs",
        should_continue,
        {
            "continue": "process_text",
            "update_job_status": "update_job_status"
        }
    )
    
    workflow.add_conditional_edges(
        "process_text",
        should_continue,
        {
            "continue": "generate_audio",
            "update_job_status": "update_job_status"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_audio",
        should_continue,
        {
            "continue": "process_audio",
            "update_job_status": "update_job_status"
        }
    )
    
    workflow.add_conditional_edges(
        "process_audio",
        should_continue,
        {
            "continue": "merge_video_audio",
            "update_job_status": "update_job_status"
        }
    )
    
    workflow.add_conditional_edges(
        "merge_video_audio",
        should_continue,
        {
            "continue": "update_job_status",
            "update_job_status": "update_job_status"
        }
    )
    
    # Add normal edges
    workflow.add_edge("update_job_status", END)
    
    return workflow.compile()


# Create the compiled workflow
compiled_workflow = create_video_generation_workflow()


class VideoGenerationWorkflow:
    """Wrapper class for the video generation workflow"""
    
    def __init__(self):
        self.workflow = compiled_workflow
    
    async def run_workflow(self, input_data: dict):
        """Run the video generation workflow with input data"""
        from app.services.tts_service import TTSManager
        from app.services.video_service import VideoProcessor
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        try:
            # Initialize services
            tts_manager = TTSManager()
            video_processor = VideoProcessor()
            
            # Prepare initial state
            initial_state = VideoGenerationState(
                input_video_path=input_data['input_file_path'],
                description_text=input_data['description_text'],
                target_language=input_data['target_language'],
                processed_text="",
                audio_path="",
                output_video_path="",
                job_id=input_data['job_id'],
                db_session=db,
                tts_manager=tts_manager,
                video_processor=video_processor,
                error_message="",
                progress=0
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Return result object
            return WorkflowResult(
                status="COMPLETED" if not result.get('error_message') else "FAILED",
                progress=result.get('progress', 100),
                output_path=result.get('output_video_path'),
                error_message=result.get('error_message')
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return WorkflowResult(
                status="FAILED",
                progress=100,
                output_path=None,
                error_message=str(e)
            )
        finally:
            db.close()


class WorkflowResult:
    """Result object for workflow execution"""
    
    def __init__(self, status: str, progress: int, output_path: str = None, error_message: str = None):
        self.status = status
        self.progress = progress
        self.output_path = output_path
        self.error_message = error_message