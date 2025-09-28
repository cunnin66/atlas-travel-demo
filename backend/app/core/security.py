from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

ph = PasswordHasher()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    # TODO: Implement JWT token creation
    pass


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token"""
    # TODO: Implement JWT refresh token creation
    pass


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    # TODO: Implement token verification
    pass


def hash_password(password: str) -> str:
    """Hash password using Argon2"""
    # TODO: Implement password hashing
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    # TODO: Implement password verification
    pass
