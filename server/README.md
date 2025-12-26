# Property Video Generator with AI Narration

An AI-powered system that generates property videos with audio descriptions in multiple languages. Users provide a property video and text description, select a language, and get back a video with synchronized audio narration.

## Features

- Upload property videos (mp4, mov, avi formats)
- Generate AI narration from text descriptions
- Support for multiple languages (English and Telugu initially)
- Job tracking with status updates
- Error handling and retry mechanisms
- FastAPI backend with asynchronous processing
- LangGraph workflow orchestration

## Tech Stack

- **Backend**: FastAPI (Python 3.9+)
- **Database**: SQLite (development), PostgreSQL ready
- **AI/ML**: LangChain + LangGraph for workflow orchestration
- **Video Processing**: FFmpeg (via ffmpeg-python)
- **TTS**: OpenAI TTS API (primary), Google Cloud TTS (backup)
- **Languages**: English (primary), Telugu (secondary), expandable to others

## Installation

### Prerequisites

- Python 3.9+
- FFmpeg installed on your system

### Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd property-video-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

Create a `.env` file with the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CLOUD_CREDENTIALS_PATH=path/to/your/google-cloud-credentials.json
```

## API Endpoints

### Video Generation

- `POST /api/v1/generate` - Submit a video generation job
  - Upload video file
  - Provide description text
  - Select target language

### Job Status

- `GET /api/v1/status/{job_id}` - Get the status of a video generation job

### Video Upload

- `POST /api/v1/upload` - Upload a video file without starting generation

### Supported Languages

- `GET /api/v1/languages` - Get list of supported languages

### Job Management

- `GET /api/v1/jobs` - List video generation jobs
- `DELETE /api/v1/jobs/{job_id}` - Delete a video generation job

## Usage

1. Upload your property video file
2. Provide a text description of the property
3. Select the target language for narration
4. Submit the job and receive a job ID
5. Poll the status endpoint to check progress
6. Download the generated video when complete

## Architecture

```
FastAPI → LangGraph Workflow → TTS Service → Audio Processing → FFmpeg Merge → Output Video
```

### Workflow Steps

1. **VALIDATION** - Validate input parameters
2. **TEXT_PROCESSING** - Process and clean text for TTS
3. **TTS_GENERATION** - Generate audio from text using TTS service
4. **AUDIO_PROCESSING** - Process audio for video merging
5. **VIDEO_MERGING** - Merge audio with original video
6. **COMPLETED** - Job completed successfully

## Development

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Code Formatting

```bash
black .
```

## Deployment

For production deployment, consider:

- Using PostgreSQL instead of SQLite
- Setting up a proper task queue (like Celery) for background jobs
- Configuring proper logging and monitoring
- Setting up reverse proxy (nginx) with SSL
- Using a WSGI/ASGI server (like Gunicorn) for production

## License

[MIT License](LICENSE)