from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DestinationBase(BaseModel):
    """Base destination schema"""

    name: str
    country: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[List[str]] = []


class DestinationCreate(DestinationBase):
    """Destination creation schema"""

    pass


class DestinationUpdate(BaseModel):
    """Destination update schema"""

    name: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[List[str]] = None


class DestinationResponse(DestinationBase):
    """Destination response schema"""

    id: int

    class Config:
        from_attributes = True
