import operator
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from typing_extensions import Annotated


class PlanRequest(BaseModel):
    """Travel plan request schema"""

    destination_id: int
    prompt: str


class NodeEvent(BaseModel):
    """Node event schema"""

    trace_id: str
    node: str
    status: str
    ts: datetime  # start?
    args_digest: Any
    result: Optional[Any] = None


class Activity(BaseModel):
    """Activity schema"""

    name: str
    description: str
    duration: Optional[int] = None  # minutes
    cost: Optional[float] = None
    location: Optional[str] = None


class DayPlan(BaseModel):
    """Day plan schema"""

    date: Optional[str] = None
    activities: List[Activity] = []
    total_cost: Optional[float] = None


class Itinerary(BaseModel):
    """Itinerary schema"""

    total_cost_usd: Optional[float] = None
    days: List[DayPlan] = []


class Citation(BaseModel):
    """Citation schema"""

    title: str
    source: str  # url | manual | file | tool
    ref: str  # "knowledge_item_id" | tool_name#id


class ToolAudit(BaseModel):
    """Tool audit schema"""

    name: str
    count: int
    total_ms: float


class PlanStep(TypedDict):
    id: str
    depends_on: List[str]
    tool: str
    args: Any


class AgentState(TypedDict):
    """Agent state schema for LangGraph workflow"""

    session_id: str
    messages: Annotated[List[BaseMessage], operator.add]
    constraints: Any
    plan: List[PlanStep]
    itinerary: Dict[str, Any]  # Will be converted to Itinerary when needed
    citations: Annotated[List[Citation], operator.add]
    decisions: List[str]
    answer_markdown: str
    done: bool


class PlanResponse(BaseModel):
    """Travel plan response schema"""

    query: str
    answer_markdown: str
    itinerary: Itinerary
    citations: Optional[List[Citation]] = []
    tools_used: Optional[List[ToolAudit]] = []
    decisions: Optional[List[str]] = []
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
