import asyncio
import json
import time
import uuid
from datetime import datetime

from app.models.agent import AgentRun
from app.models.user import User
from app.nodes.intent import IntentNode
from app.nodes.responder import ResponderNode
from app.nodes.synthesizer import SynthesizerNode
from app.schemas.agent import AgentState, Itinerary, PlanRequest, PlanResponse
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage

# from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from sqlalchemy.orm import Session


def create_system_message() -> SystemMessage:
    return SystemMessage(
        content="""You are a travel planning assistant. You are given a user request which will include different types of constraints.
        Your task is to build a travel itinerary that satisfies all the user's constraints for the trip.
        Some constraints may be missing, in which case you may make reasonable assumptions about the user's intent.
        By the end, your response must conform to the appropriate JSON format.

        In general, the itinerary should cover the following:
        - Travel dates
        - Travel budget
        - Airfare and transportation
        - Hotel accommodations
        - Weather-appropriate daily activities
        - Local tips and cultural considerations
        """
    )


class StatusUpdate(BaseModel):
    type: str = "status"
    content: str  # payload, user-facing string, error message


def create_agent_workflow():
    """Create and configure the agent workflow"""
    # Get tools from registry
    tool_executor = []  # = ToolExecutor([])
    model = ChatOpenAI(model="gpt-4o", temperature=0)

    workflow = StateGraph(AgentState)
    workflow.add_node("intent", IntentNode(model, tool_executor))
    workflow.add_node("synthesizer", SynthesizerNode(model, tool_executor))
    workflow.add_node("responder", ResponderNode(model, tool_executor))

    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "synthesizer")
    workflow.add_edge("synthesizer", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()


# Workflow is an object that executes a series of nodes on the AgentState object
# Exits when complete, meaning we need to offload the final plan
workflow = create_agent_workflow()


class AgentService:
    def __init__(self, user: User, db: Session):
        self.db = db
        self.user = user
        self.session_id = str(uuid.uuid4())

    async def create_travel_plan(self, request: PlanRequest) -> PlanResponse:
        initial_state = self._initialize_agent(request)
        final_state = await asyncio.to_thread(workflow.invoke, initial_state)

        if final_state.get("done", False):
            self._update_run_record(
                "completed",
                final_state.get("plan_snapshot", {}),
                final_state.get("tool_log", []),
            )
        else:
            self._update_run_record(
                "failed",
                final_state.get("plan_snapshot", {}),
                final_state.get("tool_log", []),
            )

        return PlanResponse(
            id=self.run.id,
            query=request.prompt,
            answer_markdown=final_state.get("answer_markdown", ""),
            itinerary=final_state.get("itinerary", {}),
            citations=final_state.get("citations", []),
            tools_used=final_state.get("tool_log", []),
            decisions=final_state.get("decisions", []),
            status=self.run.status,
            created_at=self.run.started_at,
        )

    async def stream_agent_response(self, request: PlanRequest) -> StreamingResponse:
        try:
            initial_state = self._initialize_agent(request)
            # Stream the agent workflow execution
            async for chunk in self._stream_workflow(initial_state):
                yield f"data: {json.dumps(chunk)}\n\n"

            # Send completion event
            # To get the final_state from the streamed workflow, you need to capture the last node_output from the async generator.
            # Here's an example of how you might do this:
            final_state = None
            async for chunk in self._stream_workflow(initial_state):
                yield f"data: {json.dumps(chunk)}\n\n"
                # If your stream yields the full state at the end, capture it here
                if isinstance(chunk, dict) and chunk.get("type") == "complete":
                    final_state = chunk.get("content")

            self._update_run_record(
                "completed",
                final_state.get("plan_snapshot", {}),
                final_state.get("tool_log", []),
            )
        except Exception as e:
            error_data = {
                "type": "error",
                "content": str(e),
                "session_id": self.session_id,
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            self._update_agent_run("failed")

    async def _stream_workflow(self, initial_state: AgentState) -> StreamingResponse:
        """Stream workflow execution with real-time updates"""

        # Stream workflow execution
        async for event in workflow.astream(initial_state):
            for node_name, node_output in event.items():
                if node_name == "intent":
                    msg = "Extracting constraints..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "planner":
                    msg = "Building a strategy..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "tools":
                    msg = "Deciding on the next step..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "verifier":
                    msg = "Validating itinerary constraints..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "repair":
                    msg = "Identifying potential fixes..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "synthesizer":
                    msg = "Finalizing itinerary..."
                    print(msg)
                    yield {
                        "type": "message",
                        "content": msg,
                    }
                elif node_name == "responder":
                    msg = "Done."
                    print(msg)
                    yield {
                        "type": "complete",
                        "content": node_output.get("messages", [])[-1].content,
                    }

    def _initialize_agent(self, request: PlanRequest) -> AgentState:
        self._create_run_record()
        return self._create_initial_state(request)

    def _create_run_record(self) -> AgentRun:
        self.start_time = datetime.now()
        self.run = AgentRun(
            org_id=self.user.org_id,
            user_id=self.user.id,
            session_id=self.session_id,
            plan_snapshot=None,
            tool_log=[],
            status="pending",
            started_at=self.start_time,
            ended_at=None,
        )
        self.db.add(self.run)
        self.db.commit()
        self.db.refresh(self.run)

    def _update_run_record(self, status: str, snapshot: dict, tool_log: list):
        self.run.status = status
        self.run.plan_snapshot = snapshot
        self.run.tool_log = tool_log
        if status in ["completed", "failed"]:
            self.run.ended_at = datetime.now()
        self.db.commit()
        self.db.refresh(self.run)

    def _create_initial_state(self, request: PlanRequest) -> AgentState:
        # Initialize agent state with system prompt
        return {
            "session_id": self.session_id,
            "messages": [create_system_message(), HumanMessage(content=request.prompt)],
            "constraints": {},
            "plan": [],
            "itinerary": {},
            "citations": [],
            "decisions": [],
            "answer_markdown": "",
            "done": False,
        }
