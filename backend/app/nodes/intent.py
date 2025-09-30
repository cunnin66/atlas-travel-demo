import json
from typing import Dict, List, Optional

from app.nodes.base import BaseNode
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

# Intent and Constraint Extractor
# 1. Normalize goal
# 2. Extract hard/soft constraints


class TravelDates(BaseModel):
    """Travel dates constraint"""

    start: Optional[str] = Field(
        default="", description="Start date in YYYY-MM-DD format"
    )
    end: Optional[str] = Field(default="", description="End date in YYYY-MM-DD format")


class TravelPreferences(BaseModel):
    """Travel preferences"""

    family_friendly: Optional[bool] = Field(
        default=None, description="Whether the trip should be family-friendly"
    )
    luxury: Optional[bool] = Field(
        default=None,
        description="Whether luxury accommodations/experiences are preferred",
    )
    budget_friendly: Optional[bool] = Field(
        default=None, description="Whether budget options are preferred"
    )
    adventure: Optional[bool] = Field(
        default=None, description="Whether adventure activities are desired"
    )
    cultural: Optional[bool] = Field(
        default=None, description="Whether cultural experiences are important"
    )
    relaxation: Optional[bool] = Field(
        default=None, description="Whether relaxation/leisure is the focus"
    )


class TravelConstraints(BaseModel):
    """Extracted travel constraints from user input"""

    budget_usd: Optional[float] = Field(
        default=None, description="Budget in USD, null if not specified"
    )
    dates: TravelDates = Field(default_factory=TravelDates, description="Travel dates")
    airports: List[str] = Field(
        default_factory=list, description="Departure airport codes"
    )
    preferences: TravelPreferences = Field(
        default_factory=TravelPreferences, description="Travel preferences"
    )


class IntentNode(BaseNode):
    def __call__(self, state):
        print(f"---INTENT NODE ({state['session_id']})---")

        # Create a structured output model for the LLM
        structured_llm = self.llm_model.with_structured_output(TravelConstraints)

        # System message to instruct the LLM to extract constraints
        constraint_extraction_message = SystemMessage(
            content="""You are a travel planning constraint extraction assistant. Your task is to analyze the user's travel request and extract specific constraints.

Analyze the user's message and extract travel constraints including:
- Budget in USD (if mentioned)
- Travel dates (start and end dates in YYYY-MM-DD format)
- Departure airports (airport codes if specified)
- Travel preferences (family-friendly, luxury, budget-friendly, adventure, cultural, relaxation)

Only extract information that is explicitly mentioned or strongly implied in the user's request.
If no specific constraint is mentioned, leave it as null or empty."""
        )

        # Get the user's latest message
        user_messages = [
            msg for msg in state["messages"] if hasattr(msg, "content") and msg.content
        ]
        if not user_messages:
            return {"constraints": state.get("constraints", {})}

        # Construct the prompt for constraint extraction
        prompt = [constraint_extraction_message] + user_messages[
            -1:
        ]  # Use only the latest user message

        try:
            # Call the structured LLM to extract constraints
            extracted_constraints: TravelConstraints = structured_llm.invoke(prompt)

            print(f"Extracted constraints: {extracted_constraints}")

            return {
                "constraints": extracted_constraints.dict(),
                "messages": [
                    AIMessage(
                        content=f"Extracted constraints: {extracted_constraints.dict()}"
                    )
                ],
            }

        except Exception as e:
            print(f"Failed to extract constraints: {e}")
            return {
                "constraints": state.get("constraints", {}),
                "messages": [user_messages[-1]],  # Pass through the user message
            }
