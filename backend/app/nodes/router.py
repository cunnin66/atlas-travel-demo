# ROUTER/SELECTOR
# choose which step to execute next, support parallel execution where applicable

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState


class Router:
    def __call__(self, state: AgentState):
        print(f"---ROUTER NODE (${state['session_id']})---")
        plan = state["plan"]

        if len(plan) == 0:
            return "verifier"

        if plan[0]["tool"] == "agent":
            return "planner"  # will pop task when complete

        elif plan[0]["tool"] == "decide":
            return "decide"
        else:
            # stage next jobs to be done?
            return "tool"
