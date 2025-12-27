from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import timedelta
from typing import Optional, List
from app.database import get_db
from app.services.auth_service import auth_service
from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
    ChangePasswordRequest,
    UserLoginResponse
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user from the token"""
    payload = auth_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/auth/register", response_model=UserResponse, summary="Register a new user")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with auto-generated password"""
    try:
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_user = auth_service.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Generate a password if not provided
        password = user_data.password or auth_service.generate_password()
        
        # Create the user
        user, plain_password = auth_service.create_user(
            db,
            user_data.username,
            user_data.email,
            password,
            user_data.full_name
        )
        
        # Return user response (without plain password)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            credits=user.credits,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=UserLoginResponse, summary="Login a user")
async def login_user(
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login a user and return access token"""
    user = auth_service.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    user.last_login = func.now()
    db.commit()
    
    # Record login event in system logs
    logging_service.log(db, f"User '{user.username}' authenticated successfully", level="SUCCESS", module="AUTH")

    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            credits=user.credits,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/auth/logout", summary="Logout user")
async def logout_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Logout user by invalidating session"""
    # In a real implementation, you would invalidate the token
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}


@router.get("/auth/me", response_model=UserResponse, summary="Get current user info")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        credits=current_user.credits,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/auth/me", response_model=UserResponse, summary="Update current user info")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    updated_user = auth_service.update_user(
        db,
        current_user.id,
        username=user_update.username,
        email=user_update.email,
        full_name=user_update.full_name
    )
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        credits=updated_user.credits,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.put("/auth/change-password", summary="Change user password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    success = auth_service.change_password(
        db,
        current_user.id,
        password_request.current_password,
        password_request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.get("/auth/users/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        credits=user.credits,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.get("/auth/users", response_model=List[UserResponse], summary="Get all users (admin only)")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            credits=user.credits,
            created_at=user.created_at,
            updated_at=user.updated_at
        ) for user in users
    ]