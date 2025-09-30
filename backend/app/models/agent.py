from app.models.base import BaseModel
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class AgentRun(BaseModel):
    """Agent execution run model"""

    __tablename__ = "agent_runs"

    org_id = Column(ForeignKey("orgs.id"), nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

    session_id = Column(String(255), index=True)
    plan_snapshot = Column(JSON)
    tool_log = Column(JSON, default=list)  # array of JSON objects
    status = Column(String(50))  # pending, running, completed, failed
    cost_usd = Column(Float)

    # Relationships
    user = relationship("User", back_populates="agent_runs")
    org = relationship("Org", back_populates="agent_runs")
