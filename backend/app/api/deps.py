from typing import Optional

from app.core.security import get_user_by_access_token
from app.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(security)
) -> User:
    """Get current authenticated user"""
    valid_user = get_user_by_access_token(token, db)
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return valid_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    if current_user.is_admin:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def get_redis_client():
    """Get Redis client"""
    # TODO: Implement Redis client dependency
    pass
