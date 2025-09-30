from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """Long-lived refresh token model"""
    __tablename__ = "refresh_tokens"
    
    hashed_jti = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
