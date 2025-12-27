from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import secrets
import string
from app.models.user import User, UserSession
from app.config import settings
import jwt


import bcrypt


class AuthService:
    def __init__(self):
        self.algorithm = "HS256"
        self.secret_key = settings.secret_key
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against the hashed password using bcrypt"""
        try:
            # Handle both string and bytes for hashed_password
            if isinstance(hashed_password, str):
                hashed_bytes = hashed_password.encode('utf-8')
            else:
                hashed_bytes = hashed_password
            
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_bytes)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a plain password using bcrypt"""
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return the payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get a user by username"""
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, username: str, email: str, password: str, full_name: str = None) -> Tuple[User, str]:
        """Create a new user with auto-generated password"""
        # Hash the password
        hashed_password = self.get_password_hash(password)

        # Create the user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user, password  # Return user and plain password for initial login
        except IntegrityError:
            db.rollback()
            raise ValueError("Username or email already exists")

    def update_user(self, db: Session, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Update allowed fields
        allowed_fields = {'username', 'email', 'full_name', 'is_active', 'credits'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'password':
                    value = self.get_password_hash(value)
                setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        if not self.verify_password(current_password, user.hashed_password):
            return False

        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        return True

    def generate_password(self, length: int = 12) -> str:
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_session(self, db: Session, user_id: int) -> UserSession:
        """Create a new user session"""
        # Generate a secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Set session expiration (e.g., 24 hours)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create the session
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session

    def get_session_by_token(self, db: Session, token: str) -> Optional[UserSession]:
        """Get a session by token"""
        return db.query(UserSession).filter(
            UserSession.session_token == token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()

    def invalidate_session(self, db: Session, token: str) -> bool:
        """Invalidate a session by token"""
        session = db.query(UserSession).filter(UserSession.session_token == token).first()
        if session:
            session.is_active = False
            db.commit()
            return True
        return False


# Global auth service instance
auth_service = AuthService()