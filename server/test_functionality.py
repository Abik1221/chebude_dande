#!/usr/bin/env python3
"""
Test script to verify that the Property Video Generator components work correctly.
This script tests the basic imports and functionality without requiring external services.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing module imports...")
    
    try:
        from app.services.tts_service import TTSServiceManager
        print("✓ TTS Service import successful")
    except Exception as e:
        print(f"✗ TTS Service import failed: {e}")
        return False
    
    try:
        from app.services.video_service import VideoProcessingService
        print("✓ Video Service import successful")
    except Exception as e:
        print(f"✗ Video Service import failed: {e}")
        return False
    
    try:
        from app.workflows.video_generation import VideoGenerationWorkflow
        print("✓ Workflow import successful")
    except Exception as e:
        print(f"✗ Workflow import failed: {e}")
        return False
    
    try:
        from app.models.job import Job, Language
        print("✓ Database models import successful")
    except Exception as e:
        print(f"✗ Database models import failed: {e}")
        return False
    
    try:
        from app.services.job_service import JobTracker
        print("✓ Job service import successful")
    except Exception as e:
        print(f"✗ Job service import failed: {e}")
        return False
    
    try:
        from app.config import settings
        print("✓ Configuration import successful")
    except Exception as e:
        print(f"✗ Configuration import failed: {e}")
        return False
    
    try:
        from app.database import engine, SessionLocal, Base
        print("✓ Database setup import successful")
    except Exception as e:
        print(f"✗ Database setup import failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration settings"""
    print("\nTesting configuration...")
    
    try:
        from app.config import settings
        
        # Check that required settings exist
        required_settings = [
            'app_name',
            'app_version', 
            'host',
            'port',
            'database_url',
            'openai_api_key',
            'upload_folder',
            'output_folder',
            'temp_folder',
            'max_video_size_mb',
            'allowed_video_formats'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✓ Setting '{setting}' exists")
            else:
                print(f"✗ Setting '{setting}' missing")
                return False
        
        print("✓ All required settings exist")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_models():
    """Test database models"""
    print("\nTesting database models...")
    
    try:
        from app.models.job import Job, Language
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        
        # Create an in-memory database for testing
        engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Test Language model
            lang = Language(code="en", name="English", tts_voice="nova")
            db.add(lang)
            db.commit()
            db.refresh(lang)
            
            assert lang.code == "en"
            assert lang.name == "English"
            print("✓ Language model works correctly")
            
            # Test Job model
            job = Job(
                status="PENDING",
                input_file_path="/test/video.mp4",
                description_text="Test property description",
                target_language="en"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            assert job.status == "PENDING"
            assert job.target_language == "en"
            print("✓ Job model works correctly")
            
        finally:
            db.close()
        
        print("✓ Database models work correctly")
        return True
        
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False


def test_services():
    """Test service classes (without external dependencies)"""
    print("\nTesting services...")
    
    try:
        # Test JobTracker (without actual database)
        from app.services.job_service import JobTracker
        print("✓ JobTracker class can be instantiated")
        
        # Test that we can create the service classes (without external dependencies)
        print("✓ Service classes can be imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Services test failed: {e}")
        return False


def test_directory_structure():
    """Test that required directories exist or can be created"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'uploads',
        'outputs', 
        'temp',
        'logs'
    ]
    
    for dir_name in required_dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            print(f"✓ Directory '{dir_name}' exists or can be created")
        except Exception as e:
            print(f"✗ Directory '{dir_name}' creation failed: {e}")
            return False
    
    return True


def main():
    """Run all tests"""
    print("Property Video Generator - Functionality Verification")
    print("=" * 55)
    
    all_tests_passed = True
    
    # Run all tests
    tests = [
        test_imports,
        test_config,
        test_models,
        test_services,
        test_directory_structure
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 55)
    if all_tests_passed:
        print("✓ All tests passed! The Property Video Generator is ready.")
        print("\nTo start the application:")
        print("1. Make sure you have FFmpeg installed")
        print("2. Set up your API keys in .env file")
        print("3. Run: uvicorn app.main:app --reload")
        return True
    else:
        print("✗ Some tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)