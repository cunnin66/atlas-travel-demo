from app.nodes.base import BaseNode
from app.schemas.agent import AgentState

# Verifier / Critic
# checks the itinerary/partial plan against constraints, writes violations into state
# 1. Budget
# 2. Feasibility
# 3. Weather sensitivity
# 4. Preference fit (kid_friendly, mueseum, neighborhood safety/noise level)

VERIFICATION_RULES = [
    "Ensure the planned itinerary is less than the budget constraint",
    "Ensure that the itinerary does not exceed the date constraints",
    "Ensure that no activities are scheduled at the same time",
    "Ensure that activities on the same day are sufficiently co-located",
    "If the trip is less than 10 days away, ensure that the itinerary activities are weather appropriate",
    "Ensure the chosen activities and locations fit the user's preferences",
]


class VerifierNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---VERIFIER NODE (${state['session_id']})---")

        return {"messages": [state["messages"]]}
