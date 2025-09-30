from app.nodes.base import BaseNode
from app.schemas.agent import AgentState
from langchain_core.messages import AIMessage, SystemMessage

# Planner Node
# emits a multi-step plan (ordered tool calls and joins) with dependecies and rough cost/time estimates


class PlannerNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---PLANNER NODE (${state['session_id']})---")

        planning_system_message = SystemMessage(
            content="""You are an expert travel planner. Your goal is to create a
            step-by-step plan to fulfill the user's request based on the provided
            constraints. Create an outline of the tools that need to be called,
            their arguments, and their dependencies."""
        )

        # 2. Construct the prompt by prepending the system message
        #    to the existing history from the state.
        prompt = state["messages"] + [planning_system_message]

        # 3. Call the LLM with the specialized prompt
        response = self.llm_model.invoke(prompt)

        # The response will be an AIMessage containing the plan
        return {
            "messages": [AIMessage(content=f"Plan: {response.tool_calls}")],
            "plan": [response.tool_calls],
        }
