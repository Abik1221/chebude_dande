from fastapi import APIRouter
from app.api.v1.endpoints import jobs, settings, auth
from app.api.v1 import video_generation

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
api_router.include_router(settings.router, prefix="/api/v1", tags=["settings"])
api_router.include_router(auth.router, prefix="/api/v1", tags=["auth"])
api_router.include_router(video_generation.router, prefix="/api/v1", tags=["video-generation"])