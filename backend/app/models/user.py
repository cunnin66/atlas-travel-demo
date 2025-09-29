from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=True)
    
    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)
    org = relationship("Org", back_populates="users")
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")


def scrubUser(user: User) -> User:
    """Scrub user of sensitive fields"""
    user.hashed_password = None
    user.refresh_tokens = None
    return user