from typing import List, Optional

from app.nodes.base import BaseNode
from app.schemas.agent import Activity, AgentState, Citation, DayPlan, Itinerary
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

# SYNTHESIZER
# fuses tool results + RAG passages, produces itinerary JSON + narrative + citations


class SynthesizerOutput(BaseModel):
    """Structured output schema for the synthesizer LLM"""

    itinerary: Itinerary = Field(
        description="Complete travel itinerary with activities and costs"
    )
    citations: List[Citation] = Field(
        description="Sources and references used to create the itinerary"
    )
    decisions: List[str] = Field(
        description="Key decisions made during itinerary planning"
    )
    reasoning: str = Field(
        description="Brief explanation of the planning approach and rationale"
    )


class SynthesizerNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---SYNTHESIZER NODE (${state['session_id']})---")

        # Extract current itinerary if it exists
        current_itinerary = state.get("itinerary", {})

        # Extract tool results and other relevant information from the state
        tool_results = self._extract_tool_results(state)
        constraints = state.get("constraints", {})

        # Create system message for synthesis
        system_message = SystemMessage(
            content=self._create_synthesis_prompt(
                current_itinerary, tool_results, constraints
            )
        )

        # Prepare the full message history with system prompt
        messages = [system_message] + state["messages"]

        # Use structured output to get properly formatted response
        structured_llm = self.llm_model.with_structured_output(SynthesizerOutput)
        result = structured_llm.invoke(messages)

        print(f"Synthesizer result: {result}")

        # Convert the structured result to the expected format
        itinerary_dict = result.itinerary.model_dump()
        citations_list = [citation.model_dump() for citation in result.citations]

        return {
            "messages": [
                AIMessage(
                    content=f"Synthesized itinerary with {len(result.itinerary.days)} days. {result.reasoning}"
                )
            ],
            "itinerary": itinerary_dict,
            "citations": citations_list,
            "decisions": result.decisions,
        }

    def _extract_tool_results(self, state: AgentState) -> str:
        """Extract and format tool results from the agent state"""
        tool_results = []

        # Look for tool results in the message history
        for message in state["messages"]:
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_results.append(f"Tool: {tool_call.get('name', 'unknown')}")
                    tool_results.append(f"Args: {tool_call.get('args', {})}")

            # Also check for tool responses
            if hasattr(message, "content") and isinstance(message.content, str):
                if (
                    "weather" in message.content.lower()
                    or "flight" in message.content.lower()
                ):
                    tool_results.append(f"Tool result: {message.content}")

        # Include plan information if available
        if state.get("plan"):
            tool_results.append(f"Executed plan with {len(state['plan'])} steps")
            for step in state["plan"]:
                tool_results.append(
                    f"- {step.get('tool', 'unknown')}: {step.get('args', {})}"
                )

        return "\n".join(tool_results) if tool_results else "No tool results available"

    def _create_synthesis_prompt(
        self, current_itinerary: dict, tool_results: str, constraints: dict
    ) -> str:
        """Create a comprehensive system prompt for synthesis"""
        return f"""You are a travel planning synthesizer. Your task is to create a comprehensive, detailed travel itinerary by combining:

1. The user's conversation history and requests
2. Current itinerary information (if any): {current_itinerary}
3. Tool results and data: {tool_results}
4. Travel constraints: {constraints}

Your responsibilities:
- Create a detailed, day-by-day itinerary with specific activities
- Include realistic costs, durations, and locations for each activity
- Provide proper citations for all information sources
- Document key planning decisions made
- Feel free to add helpful information you know about destinations, activities, or travel tips
- Ensure activities are weather-appropriate and logistically feasible
- Balance different types of activities (cultural, recreational, dining, etc.)

Guidelines:
- Each activity should have a clear name, description, duration (in minutes), cost (in USD), and location
- Daily costs should sum up correctly
- Include a variety of activities throughout each day
- Consider travel time between locations
- Provide practical, actionable recommendations
- Use real-world knowledge to enhance the itinerary with specific venues, restaurants, or attractions when appropriate

Output format:
- itinerary: Complete structured itinerary following the schema
- citations: List sources used (tools, knowledge base, general knowledge)
- decisions: Key planning decisions and trade-offs made
- reasoning: Brief explanation of your planning approach

Be comprehensive and helpful - this itinerary should be ready for the traveler to use."""
