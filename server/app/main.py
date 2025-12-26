from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.database import create_all_tables
from app.config import settings
from seed_user import seed_admin_user

app = FastAPI(
    title="EstateVision AI - Property Video Generator API",
    description="API for generating property videos with AI narration",
    version="1.0.0"
)

# Initialize database tables and seed admin user
create_all_tables()
seed_admin_user()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "EstateVision AI - Property Video Generator API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}