from app.schemas.agent import AgentState


class BaseNode:
    def __init__(self, llm_model, tool_executor):
        self.llm_model = llm_model
        self.tool_executor = tool_executor

    def __call__(self, state: AgentState):
        raise NotImplementedError("Subclasses must implement __call__")
