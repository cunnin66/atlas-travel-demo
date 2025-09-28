from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import BaseModel


class KnowledgeItem(BaseModel):
    """Knowledge base item model"""
    __tablename__ = "knowledge_items"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String(50))  # file, url, manual, etc.
    source_url = Column(String(500))
    metadata = Column(JSON)
    tags = Column(ARRAY(String))
    
    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="knowledge_item")


class Embedding(BaseModel):
    """Vector embedding model"""
    __tablename__ = "embeddings"
    
    knowledge_item_id = Column(ForeignKey("knowledge_items.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(ARRAY(Float))  # Vector embedding
    chunk_index = Column(String(50))
    
    # Relationships
    knowledge_item = relationship("KnowledgeItem", back_populates="embeddings")
