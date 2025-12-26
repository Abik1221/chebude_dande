from fastapi import APIRouter, Form, File, UploadFile, Depends
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

test_router = APIRouter()

@test_router.post("/test-form")
async def test_form_data(
    description_text: str = Form(...),
    target_language: str = Form(...),
    video_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return {
        "description_text": description_text,
        "target_language": target_language,
        "video_filename": video_file.filename,
        "user": current_user.username
    }