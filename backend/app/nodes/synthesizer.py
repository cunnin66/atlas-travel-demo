from app.nodes.base import BaseNode
from app.schemas.agent import AgentState
from langchain_core.messages import AIMessage

# SYNTHESIZER
# fuses tool results + RAG passages, produces itinerary JSON + narrative + citations


class SynthesizerNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---SYNTHESIZER NODE (${state['session_id']})---")
        # structured_llm = self.llm_model.structured_output(Itinerary)
        # result = structured_llm.invoke(state["messages"])
        itinerary = {
            "total_cost_usd": 150.0,
            "days": [
                {
                    "date": "2025-01-01",
                    "activities": [
                        {
                            "name": "Morning Coffee & Planning",
                            "description": "Start the day with local coffee and review the itinerary",
                            "duration": 60,
                            "cost": 15.0,
                            "location": "Local Café",
                        },
                        {
                            "name": "City Walking Tour",
                            "description": "Explore the historic downtown area with a guided tour",
                            "duration": 180,
                            "cost": 45.0,
                            "location": "Downtown Historic District",
                        },
                    ],
                    "total_cost": 60.0,
                },
                {
                    "date": "2025-01-02",
                    "activities": [
                        {
                            "name": "Museum Visit",
                            "description": "Visit the main city museum to learn about local history",
                            "duration": 120,
                            "cost": 20.0,
                            "location": "City Museum",
                        },
                        {
                            "name": "Local Market Shopping",
                            "description": "Browse local crafts and souvenirs at the artisan market",
                            "duration": 120,
                            "cost": 70.0,
                            "location": "Artisan Market",
                        },
                    ],
                    "total_cost": 90.0,
                },
            ],
        }
        citations = [
            {
                "title": "Local Tourism Guide",
                "source": "manual",
                "ref": "tourism_guide_2024",
            },
            {
                "title": "Restaurant Reviews Database",
                "source": "tool",
                "ref": "reviews_tool#123",
            },
        ]
        decisions = [
            "Decision 1",
            "Decision 2",
            "Decision 3",
        ]
        return {
            "messages": [AIMessage(content=f"Proposed itinerary: {itinerary}")],
            "itinerary": itinerary,
            "citations": citations,
            "decisions": decisions,
        }
