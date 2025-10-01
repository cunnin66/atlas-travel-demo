# REPAIR / RE-PLANNER
# mutates choices (airport/hotel/day order) and re-executes only affected steps

import uuid
from typing import List

from app.nodes.base import BaseNode
from app.nodes.planner import TOOL_REGISTRY, PlanSchema
from app.schemas.agent import AgentState, PlanStep
from langchain_core.messages import AIMessage, SystemMessage


class RepairNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---PLANNER NODE ({state['session_id']})---")

        current_itinerary = state.get("itinerary", {})
        violations = state.get("violations", [])
        tool_descriptions = self._generate_tool_descriptions()

        planning_system_message = SystemMessage(
            content=f"""You are a travel planning assistant. Its been identified the the following itinerary has a number of issues.
            Your task is to build a simple step-by-step plan to fix the listed issues.

Your plan should:
1. Break down the issues into logical steps
2. Use appropriate tools to gather additional information, if needed
3. Ensure each step has all necessary information
4. Create dependencies between steps when needed
5. Assume that after all steps are executed, a final 'synthesizer' and 'validator' step will be run to put it all together. So do not include them in your plan.

The current itinerary:
{current_itinerary}

The identified issues:
{violations}

Available tools to remediate:
{tool_descriptions}

Each step must have:
- id: unique identifier (e.g., "get_weather", "search_flights")
- depends_on: list of step IDs this step depends on (empty list [] if no dependencies)
- tool: exact name of the tool to use (must match available tools)
- args: dictionary with arguments for the tool

Example repair plan for a trip to Paris:
[
  {{
    "id": "search_hotels_paris",
    "depends_on": [],
    "tool": "hotel_search",
    "args": {{"location": "Paris", "check_in_date": "2025-06-01", "check_out_date": "2025-06-07"}}
  }},
  {{
    "id": "change_hotel",
    "depends_on": ["search_hotels_paris"],
    "tool": "agent",
    "args": {{"prompt": "Pick a hotel closer to the city center, per the users request"}}
  }}
]

Create a comprehensive plan that addresses the user's travel request."""
        )

        # Construct the prompt by prepending the system message to the existing history
        prompt = state["messages"] + [planning_system_message]

        # Use structured output to get a proper plan
        structured_llm = self.llm_model.with_structured_output(PlanSchema)
        response = structured_llm.invoke(prompt)
        print("Number of steps in plan:", len(response["steps"]))

        # The response should be a list of PlanStep objects
        return {
            "messages": [
                AIMessage(
                    content=f"Created new plan with {len(response['steps'])} steps"
                )
            ],
            "plan": response["steps"],
        }

    def _generate_tool_descriptions(self) -> str:
        """Generate formatted descriptions of available tools"""
        descriptions = []

        for tool_name, tool_info in TOOL_REGISTRY.items():
            desc = f"- {tool_name}: {tool_info['description']}"

            # Add argument information
            if "args" in tool_info:
                args_desc = ", ".join(
                    [
                        f"{arg}: {arg_type.__name__}"
                        for arg, arg_type in tool_info["args"].items()
                    ]
                )
                desc += f"\n  Arguments: {args_desc}"

            # Add endpoint information for HTTP tools
            if tool_info.get("type") == "http" and "endpoint" in tool_info:
                desc += f"\n  Endpoint: {tool_info['endpoint']}"

            descriptions.append(desc)

        return "\n".join(descriptions)
