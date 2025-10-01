from app.models.base import BaseModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship


class KnowledgeItem(BaseModel):
    """Knowledge base item model"""

    __tablename__ = "knowledge_items"

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String(50))  # file, url, manual, etc.
    source_url = Column(String(500))
    item_metadata = Column(JSON)
    tags = Column(ARRAY(String))

    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)

    # Destination relationship
    destination_id = Column(ForeignKey("destinations.id"), nullable=True)

    # Relationships
    embeddings = relationship("Embedding", back_populates="knowledge_item")
    destination = relationship("Destination", backref="knowledge_items")


class Embedding(BaseModel):
    """Vector embedding model"""

    __tablename__ = "embeddings"

    knowledge_item_id = Column(ForeignKey("knowledge_items.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(1536))  # OpenAI ada-002 embedding dimension
    chunk_index = Column(Integer)
    token_count = Column(Integer)

    # Relationships
    knowledge_item = relationship("KnowledgeItem", back_populates="embeddings")
