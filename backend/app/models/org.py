from app.models.base import BaseModel
from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship


class Org(BaseModel):
    """Organization model"""

    __tablename__ = "orgs"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="org")
