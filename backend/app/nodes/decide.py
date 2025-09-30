# DECIDER NODE
# decides which tool to call next

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState
from langchain_core.messages import AIMessage


class DeciderNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---DECIDER NODE (${state['session_id']})---")
        decision_step = state["plan"].pop(0)
        remaining_plan = state["plan"]

        node_prompt = [state.messages] + [decision_step]
        partialItinerary = self.llm_model.invoke(node_prompt)
        return {
            "messages": [AIMessage(content=f"Decision: {partialItinerary.content}")],
            "working_set": {},
            "plan": remaining_plan,
        }
