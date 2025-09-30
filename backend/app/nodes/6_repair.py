# REPAIR / RE-PLANNER
# mutates choices (airport/hotel/day order) and re-executes only affected steps

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState


class RepairNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---REPAIR NODE (${state['session_id']})---")
        violations = state["violations"]

        return {"messages": [state["messages"]]}
