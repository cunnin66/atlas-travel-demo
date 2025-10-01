from typing import List, TypedDict

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState, PlanStep
from langchain_core.messages import AIMessage, SystemMessage

# Planner Node
# emits a multi-step plan (ordered tool calls and joins) with dependecies and rough cost/time estimates

TOOL_REGISTRY = {
    "agent": {
        "type": "local",
        "description": "A decision making agent that can decide between multiple options.",
        "args": {"prompt": str},
    },
    "weather": {
        "type": "http",
        "description": "Get current weather and forecast for a location using Open-Meteo API. Useful for travel planning.",
        "endpoint": "https://api.open-meteo.com/v1/forecast",
        "geocoding_endpoint": "https://geocoding-api.open-meteo.com/v1/search",
        "args": {"location": str, "days": int},
    },
    "search_flights": {
        "type": "api",
        "description": "Search for flights between two locations. Useful for travel planning and booking.",
        "args": {
            "origin": str,
            "destination": str,
            "departure_date": str,
        },
    },
    "knowledge_base": {
        "type": "rag",
        "description": "Search the knowledge base using RAG (Retrieval Augmented Generation). Provides relevant information from uploaded documents, travel guides, and other knowledge sources.",
        "args": {
            "query": str,
            "limit": int,
        },
    },
    "hotel_search": {
        "type": "fixture",
        "description": "Search for hotels in a location. Useful for travel planning and booking.",
        "args": {
            "city": str,
            "country": str,
            "check_in_date": str,
            "check_out_date": str,
            "adults": int,
        },
    },
}


class PlanSchema(TypedDict):
    steps: List[PlanStep]


class PlannerNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---PLANNER NODE ({state['session_id']})---")

        # Generate tool descriptions for the system message
        tool_descriptions = self._generate_tool_descriptions()

        planning_system_message = SystemMessage(
            content=f"""You are a travel planning assistant. For the given request, create a detailed step-by-step plan using the available tools.

Your plan should:
1. Break down the user's request into logical steps
2. Use appropriate tools to gather information
3. Ensure each step has all necessary information
4. Create dependencies between steps when needed
5. Assume that after all steps are executed, a final 'synthesizer' and 'validator' step will be run. So do not include them in your plan.

Available tools:
{tool_descriptions}

Each step must have:
- id: unique identifier (e.g., "get_weather", "search_flights")
- depends_on: list of step IDs this step depends on (empty list [] if no dependencies)
- tool: exact name of the tool to use (must match available tools)
- args: dictionary with arguments for the tool

Example for a trip to Paris:
[
  {{
    "id": "check_weather",
    "depends_on": [],
    "tool": "weather",
    "args": {{"location": "Paris", "days": 7}}
  }},
  {{
    "id": "find_flight_CDG",
    "depends_on": [],
    "tool": "search_flights",
    "args": {{"origin": "JFK", "destination": "CDG", "departure_date": "2025-06-01"}}
  }},
  {{
    "id": "find_flight_ORY",
    "depends_on": [],
    "tool": "search_flights",
    "args": {{"origin": "JFK", "destination": "ORY", "departure_date": "2025-06-01"}}
  }},
  {{
    "id": "pick_airport",
    "depends_on": ["find_flight_CDG", "find_flight_ORY"],
    "tool": "agent",
    "args": {{"prompt": "Determine the best airport to fly into for the trip based on the given dates"}}
  }}
]

Create a comprehensive plan that addresses the user's travel request."""
        )

        # Construct the prompt by prepending the system message to the existing history
        prompt = [planning_system_message] + state["messages"]

        # Use structured output to get a proper plan
        structured_llm = self.llm_model.with_structured_output(PlanSchema)
        response = structured_llm.invoke(prompt)
        print("Number of steps in plan:", len(response["steps"]))

        # The response should be a list of PlanStep objects
        return {
            "messages": [
                AIMessage(content=f"Created plan with {len(response['steps'])} steps")
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
