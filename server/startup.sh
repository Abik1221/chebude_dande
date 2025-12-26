#!/bin/bash
# Startup script for Property Video Generator

echo "Starting Property Video Generator..."

# Create necessary directories
mkdir -p uploads outputs temp logs

# Initialize the database
python init_db.py

# Start the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload