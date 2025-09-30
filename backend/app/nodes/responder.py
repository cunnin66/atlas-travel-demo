# RESPONDER NODE
# streams tokens/progress and assembles final result payload
# Updates state with final markdown response

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState
from langchain_core.messages import AIMessage, SystemMessage


class ResponderNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---RESPONDER NODE (${state['session_id']})---")
        # Itinerary, citations, and decisions comes from synthesizer
        # Generate final markdown summary
        markdown = self.llm_model.invoke(
            state["messages"]
            + [
                SystemMessage(
                    content="Summarize the itinerary, citations, and decisions into a markdown write up. Only return the markdown."
                )
            ]
        )

        # Extract the content from the AIMessage
        answer_markdown = (
            markdown.content if hasattr(markdown, "content") else str(markdown)
        )

        return {
            "messages": [AIMessage(content=answer_markdown)],
            "answer_markdown": answer_markdown,
            "done": True,
        }
