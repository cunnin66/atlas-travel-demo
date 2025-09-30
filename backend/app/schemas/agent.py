from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PlanRequest(BaseModel):
    """Travel plan request schema"""

    destination: str
    duration: int  # days
    budget: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = {}
    group_size: Optional[int] = 1


class Activity(BaseModel):
    """Activity schema"""

    name: str
    description: str
    duration: Optional[int] = None  # minutes
    cost: Optional[float] = None
    location: Optional[str] = None


class DayPlan(BaseModel):
    """Day plan schema"""

    day: int
    date: Optional[str] = None
    activities: List[Activity] = []
    total_cost: Optional[float] = None


class Itinerary(BaseModel):
    """Itinerary schema"""

    destination: str
    duration: int
    total_budget: Optional[float] = None
    days: List[DayPlan] = []
    recommendations: Optional[List[str]] = []


class PlanResponse(BaseModel):
    """Travel plan response schema"""

    id: int
    query: str
    itinerary: Itinerary
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
