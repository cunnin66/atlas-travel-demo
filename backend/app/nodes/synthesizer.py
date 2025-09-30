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
            "days": [
                {
                    "date": "2025-01-01",
                    "items": [
                        {
                            "start": "10:00",
                            "end": "11:00",
                            "title": "Activity 1",
                            "location": "Location 1",
                            "notes": "Description 1",
                            "cost": 100,
                        }
                    ],
                },
            ],
            "total_cost_usd": 100,
        }
        citations = [
            {"title": "Citation 1", "source": "tool#name", "ref": "knowledge_item_id"},
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
