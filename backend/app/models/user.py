from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)
    org = relationship("Org", back_populates="users")
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")


class RefreshToken(BaseModel):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"
    
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
