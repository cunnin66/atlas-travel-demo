from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AgentRun(BaseModel):
    """Agent execution run model"""
    __tablename__ = "agent_runs"
    
    user_id = Column(ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), index=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    status = Column(String(50))  # pending, running, completed, failed
    execution_time = Column(Float)  # in seconds
    run_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="agent_runs")
