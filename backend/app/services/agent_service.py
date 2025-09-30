import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict

from app.models.agent import AgentRun
from app.models.user import User
from app.nodes.intent import IntentNode
from app.nodes.planner import PlannerNode
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
        If the user does not specify a place of origin, assume they are traveling from New York City.
        You will be asked to build a simple step-by-step plan to fufill the user's request.
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


def create_agent_workflow():
    """Create and configure the agent workflow"""
    # Get tools from registry
    tool_executor = []  # = ToolExecutor([])
    model = ChatOpenAI(model="gpt-4o", temperature=0)

    workflow = StateGraph(AgentState)
    workflow.add_node("intent", IntentNode(model, tool_executor))
    workflow.add_node("planner", PlannerNode(model, tool_executor))
    workflow.add_node("synthesizer", SynthesizerNode(model, tool_executor))
    workflow.add_node("responder", ResponderNode(model, tool_executor))

    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "planner")
    workflow.add_edge("planner", "synthesizer")
    workflow.add_edge("synthesizer", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()


# Workflow is an object that executes a series of nodes on the AgentState object
# Exits when complete, meaning we need to offload the final plan
workflow = create_agent_workflow()

# In-memory storage for plans (in production, this would be in a database)
plans_storage: Dict[str, Dict] = {}


class AgentService:
    def __init__(self, user: User, db: Session):
        self.db = db
        self.user = user
        self.session_id = str(uuid.uuid4())
        self._current_plan_id = None

    async def create_travel_plan(self, request: PlanRequest) -> PlanResponse:
        # Store the plan_id for modifications
        self._current_plan_id = request.plan_id

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

        # Generate or reuse plan ID
        is_modification = request.plan_id is not None
        if is_modification:
            plan_id = request.plan_id
        else:
            plan_id = str(uuid.uuid4())

        plan_response = PlanResponse(
            plan_id=plan_id,
            query=request.prompt,
            answer_markdown=final_state.get("answer_markdown", ""),
            itinerary=final_state.get("itinerary", {}),
            citations=final_state.get("citations", []),
            tools_used=final_state.get("tool_log", []),
            decisions=final_state.get("decisions", []),
            status=self.run.status,
            created_at=self.run.started_at,
        )

        # Store the plan with constraints for future modifications
        plans_storage[plan_id] = {
            "plan": plan_response.dict(),
            "constraints": final_state.get("constraints", {}),
        }

        return plan_response

    async def stream_agent_response(self, request: PlanRequest):
        try:
            # Store the plan_id for modifications
            self._current_plan_id = request.plan_id

            # Check if this is a modification request
            is_modification = request.plan_id is not None
            if is_modification and request.plan_id not in plans_storage:
                error_data = {
                    "type": "error",
                    "content": f"Plan with ID {request.plan_id} not found",
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                return

            initial_state = self._initialize_agent(request)
            final_state = None

            # Stream the agent workflow execution
            async for chunk in self._stream_workflow(initial_state):
                yield f"data: {json.dumps(chunk)}\n\n"

                # Capture final state when workflow completes
                if isinstance(chunk, dict) and chunk.get("type") == "plan_complete":
                    final_state = chunk

            # Update run record with completion status
            if final_state:
                self._update_run_record(
                    "completed",
                    final_state.get("plan_data", {}),
                    final_state.get("tool_log", []),
                )
            else:
                self._update_run_record("completed", {}, [])

        except Exception as e:
            error_data = {
                "type": "error",
                "content": str(e),
                "session_id": self.session_id,
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            self._update_run_record("failed", {}, [])

    async def _stream_workflow(self, initial_state: AgentState):
        """Stream workflow execution with real-time updates"""

        # Check if this is a modification request
        is_modification = initial_state.get("previous_constraints") is not None

        # Define status messages for each node
        if is_modification:
            node_messages = {
                "intent": "🔄 Analyzing your modification request...",
                "planner": "📝 Updating your travel strategy...",
                "synthesizer": "✨ Rebuilding your itinerary...",
                "responder": "🎯 Finalizing your updated plan...",
            }
        else:
            node_messages = {
                "intent": "🚀 Understanding your travel preferences...",
                "planner": "🌍 Building your travel strategy...",
                "synthesizer": "📅 Creating your personalized itinerary...",
                "responder": "✅ Finalizing your travel plan...",
            }

        current_node = None
        accumulated_state = initial_state.copy()

        # Stream workflow execution
        async for event in workflow.astream(initial_state):
            for node_name, node_output in event.items():
                # Emit status message when starting a new node
                if node_name != current_node and node_name in node_messages:
                    current_node = node_name
                    yield {
                        "type": "status",
                        "content": node_messages[node_name],
                    }
                    # Add a small delay to make the streaming feel more natural
                    await asyncio.sleep(1)

                # Accumulate state from each node
                accumulated_state.update(node_output)

        # Generate the final plan response
        if accumulated_state.get("done"):
            print(f"Accumulated state: {accumulated_state}")

            itinerary_dict = accumulated_state.get("itinerary", {})
            try:
                itinerary = (
                    Itinerary(**itinerary_dict) if itinerary_dict else Itinerary()
                )
            except Exception as e:
                print(f"Error creating Itinerary object: {e}")
                print(f"Itinerary dict was: {itinerary_dict}")
                itinerary = Itinerary()

            # Create a plan response
            plan_response = PlanResponse(
                query=initial_state["messages"][-1].content,
                answer_markdown=accumulated_state.get("answer_markdown", ""),
                itinerary=itinerary,
                citations=accumulated_state.get("citations", []),
                tools_used=[],  # TODO: Add tool usage tracking
                decisions=accumulated_state.get("decisions", []),
                status="completed",
                created_at=datetime.now(),
            )

            # Generate or reuse plan ID
            if is_modification:
                # For modifications, we need to get the plan_id from the request
                # We'll need to pass this through the initial state
                plan_id = getattr(self, "_current_plan_id", str(uuid.uuid4()))
            else:
                plan_id = str(uuid.uuid4())
            plan_response.plan_id = plan_id

            # Store the plan with constraints for future modifications
            plans_storage[plan_id] = {
                "plan": plan_response.dict(),
                "constraints": accumulated_state.get("constraints", {}),
            }

            # Create final response matching fakeStream format
            final_response = {
                "type": "plan_complete",
                "plan_id": plan_id,
                "is_edit": is_modification,
                "plan": plan_response.model_dump(mode="json"),
            }

            print(f"Sending final response: {final_response}")
            yield final_response

        # Send completion signal - this will be wrapped with "data: " by stream_agent_response
        yield "[DONE]"

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
        # Check if this is a modification request
        previous_constraints = None
        if request.plan_id:
            stored_plan = plans_storage.get(request.plan_id)
            if stored_plan:
                previous_constraints = stored_plan.get("constraints")

        # Initialize agent state with system prompt
        return {
            "session_id": self.session_id,
            "messages": [create_system_message(), HumanMessage(content=request.prompt)],
            "constraints": {},
            "previous_constraints": previous_constraints,
            "plan": [],
            "itinerary": {},
            "citations": [],
            "decisions": [],
            "answer_markdown": "",
            "done": False,
        }
