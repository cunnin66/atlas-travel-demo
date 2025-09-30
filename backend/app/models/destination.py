from app.models.base import BaseModel
from sqlalchemy import JSON, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship


class Destination(BaseModel):
    """Destination model"""

    __tablename__ = "destinations"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Organization relationship
    org_id = Column(ForeignKey("orgs.id"), nullable=False)

    # Relationships can be added later if needed
