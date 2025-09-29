from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import BaseModel


class Destination(BaseModel):
    """Destination model"""
    __tablename__ = "destinations"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)
    
    # Relationships
    knowledge_items = relationship("KnowledgeItem", back_populates="destination")
