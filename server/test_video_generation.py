#!/usr/bin/env python3
"""
Simple test script to debug the video generation endpoint
"""

import requests
import os

# Get auth token first
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={"username": "admin", "password": "TempPass123"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✓ Login successful, token: {token[:20]}...")
    
    # Test video generation
    with open("test_video.mp4", "rb") as video_file:
        files = {"video_file": video_file}
        data = {
            "description_text": "Test video description for property",
            "target_language": "en"
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            "http://localhost:8000/api/v1/generate",
            headers=headers,
            files=files,
            data=data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
else:
    print(f"✗ Login failed: {login_response.text}")