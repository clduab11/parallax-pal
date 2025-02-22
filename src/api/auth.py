from datetime import datetime, timedelta
from typing import Optional, Union
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models
from .database import get_db
from .config import settings, get_security_settings
from .monitoring import structured_logger

# Security context for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API key scheme
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    security_settings = get_security_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=security_settings['token_expire_minutes'])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        security_settings['secret_key'],
        algorithm=security_settings['algorithm']
    )
def decode_token(token: str) -> dict:
    """Decode JWT token"""
    security_settings = get_security_settings()
    try:
        payload = jwt.decode(
            token,
            security_settings['secret_key'],
            algorithms=[security_settings['algorithm']]
        )
        return payload
    except PyJWTError:
        return None


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    security_settings = get_security_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=security_settings['refresh_token_expire_days'])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        security_settings['secret_key'],
        algorithm=security_settings['algorithm']
    )
    return encoded_jwt
    return encoded_jwt

def create_api_key(db: Session, user: models.User, name: str, expires_in_days: Optional[int] = None) -> models.APIKey:
    """Create a new API key for a user"""
    api_key = models.APIKey(
        key=f"pk_{pwd_context.hash(f'{user.id}_{datetime.utcnow().timestamp()}')[-32:]}",
        name=name,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        security_settings = get_security_settings()
        payload = jwt.decode(
            token,
            security_settings['secret_key'],
            algorithms=[security_settings['algorithm']]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .filter(models.User.is_active == True)
        .first()
    )
    if user is None:
        raise credentials_exception

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user

async def get_api_key_user(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> models.User:
    """Get user from API key"""
    api_key_obj = (
        db.query(models.APIKey)
        .filter(models.APIKey.key == api_key)
        .filter(models.APIKey.is_active == True)
        .first()
    )
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
        
    # Update last used timestamp
    api_key_obj.last_used = datetime.utcnow()
    db.commit()
    
    user = (
        db.query(models.User)
        .filter(models.User.id == api_key_obj.user_id)
        .filter(models.User.is_active == True)
        .first()
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key user"
        )
        
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Verify user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_admin_role(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """Check if user has admin role"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def has_research_task_access(
    task: models.ResearchTask,
    user: models.User
) -> bool:
    """Check if user has access to research task"""
    return (
        user.role == models.UserRole.ADMIN or
        task.owner_id == user.id
    )

def log_auth_activity(
    db: Session,
    user: models.User,
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None
):
    """Log authentication/authorization activity"""
    log = models.AuditLog(
        user_id=user.id,
        action=action,
        resource_type="auth",
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    db.add(log)
    db.commit()

    structured_logger.log("info", "Auth activity",
        user_id=user.id,
        action=action,
        ip_address=ip_address
    )