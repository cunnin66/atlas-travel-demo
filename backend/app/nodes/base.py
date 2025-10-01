from typing import Any, Dict

from app.schemas.agent import AgentState
from pydantic import BaseModel


class BaseNode:
    def __init__(self, llm_model, tool_executor):
        self.llm_model = llm_model
        self.tool_executor = tool_executor

    def __call__(self, state: AgentState):
        raise NotImplementedError("Subclasses must implement __call__")


class BaseTool(BaseModel):
    """Base class for all agent tools"""

    name: str
    description: str

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Subclasses must implement execute method")

    def get_args_schema(self) -> BaseModel:
        """Return the pydantic schema for tool arguments"""
        raise NotImplementedError("Subclasses must implement get_args_schema method")
