import asyncio
import json
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List

# Increase recursion limit to handle complex workflows
sys.setrecursionlimit(2000)

from app.models.agent import AgentRun
from app.models.user import User
from app.nodes.executor import ExecutorNode
from app.nodes.intent import IntentNode
from app.nodes.planner import PlannerNode
from app.nodes.repair import RepairNode
from app.nodes.responder import ResponderNode
from app.nodes.synthesizer import SynthesizerNode
from app.nodes.verifier import VerifierNode
from app.schemas.agent import (
    AgentState,
    Itinerary,
    PlanRequest,
    PlanResponse,
    ToolAudit,
    ToolCall,
)
from langchain_core.messages import HumanMessage, SystemMessage

# from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
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
    workflow.add_node("executor", ExecutorNode(model, tool_executor))
    workflow.add_node("validator", VerifierNode(model, tool_executor))
    workflow.add_node("repair", RepairNode(model, tool_executor))
    workflow.add_node("synthesizer", SynthesizerNode(model, tool_executor))
    workflow.add_node("responder", ResponderNode(model, tool_executor))

    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "planner")

    def router_decision(state: AgentState):
        """Route based on whether there are more plan steps to execute"""
        plan = state.get("plan", [])
        if len(plan) == 0:
            return "synthesizer"
        else:
            return "executor"  # Continue executing plan steps

    workflow.add_conditional_edges("planner", router_decision)
    workflow.add_conditional_edges("executor", router_decision)
    workflow.add_edge("synthesizer", "validator")

    def validator_router(state: AgentState):
        """Route based on whether violations were found"""
        violations = state.get("violations", [])
        if len(violations) == 0:
            return "responder"
        else:
            return "repair"

    workflow.add_conditional_edges("validator", validator_router)
    workflow.add_conditional_edges("repair", router_decision)
    workflow.add_edge("responder", END)

    # Configure workflow with higher limits to handle complex plans
    return workflow.compile(
        checkpointer=None,  # No checkpointing for now
        interrupt_before=None,
        interrupt_after=None,
        debug=False,  # Enable debug mode for better error reporting
    )


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
        final_state = await asyncio.to_thread(
            workflow.invoke, initial_state, config={"recursion_limit": 20}
        )

        if final_state.get("done", False):
            self._update_run_record(
                "completed",
                final_state.get("plan_snapshot", {}),
                self._convert_tool_calls_to_log(final_state.get("tool_calls", [])),
            )
        else:
            self._update_run_record(
                "failed",
                final_state.get("plan_snapshot", {}),
                self._convert_tool_calls_to_log(final_state.get("tool_calls", [])),
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
            tools_used=self._convert_tool_calls_to_audit(
                final_state.get("tool_calls", [])
            ),
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
                    self._convert_tool_calls_to_log(final_state.get("tool_calls", [])),
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
        is_modification = getattr(self, "_current_plan_id", None) is not None

        # Define status messages for each node
        if is_modification:
            node_messages = {
                "intent": "🔄 Analyzing your modification request...",
                "planner": "📝 Updating your travel strategy...",
                "executor": "🔧 Executing travel research tasks...",
                "synthesizer": "✨ Rebuilding your itinerary...",
                "validator": "🔍 Validating your updated plan...",
                "repair": "🔧 Fixing identified issues...",
                "responder": "🎯 Finalizing your updated plan...",
            }
        else:
            node_messages = {
                "intent": "🚀 Understanding your travel preferences...",
                "planner": "🌍 Building your travel strategy...",
                "executor": "🔍 Gathering travel information...",
                "synthesizer": "📅 Creating your personalized itinerary...",
                "validator": "🔍 Checking your itinerary for issues...",
                "repair": "🔧 Optimizing your travel plan...",
                "responder": "✅ Finalizing your travel plan...",
            }

        current_node = None
        accumulated_state = initial_state.copy()

        # Stream workflow execution with increased recursion limit
        async for event in workflow.astream(
            initial_state, config={"recursion_limit": 20}
        ):
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
                tools_used=self._convert_tool_calls_to_audit(
                    accumulated_state.get("tool_calls", [])
                ),
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

            # Create final response
            final_response = {
                "type": "plan_complete",
                "plan_id": plan_id,
                "is_edit": is_modification,
                "plan": plan_response.model_dump(mode="json"),
            }

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
        constraints = {}
        if request.plan_id:
            stored_plan = plans_storage.get(request.plan_id)
            if stored_plan:
                # For modifications, start with the previous constraints
                # The intent node will merge these with the new modification request
                constraints = stored_plan.get("constraints", {})

        # Initialize agent state with system prompt
        return {
            "session_id": self.session_id,
            "messages": [create_system_message(), HumanMessage(content=request.prompt)],
            "constraints": constraints,
            "plan": [],
            "tool_calls": [],
            "itinerary": {},
            "citations": [],
            "decisions": [],
            "violations": [],
            "answer_markdown": "",
            "done": False,
        }

    def _convert_tool_calls_to_log(self, tool_calls: List[ToolCall]) -> List[Dict]:
        """Convert ToolCall objects to log format for database storage"""
        return [
            {
                "id": tc.id,
                "tool": tc.tool,
                "args": tc.args,
                "result": tc.result,
                "error": tc.error,
                "started_at": tc.started_at.isoformat() if tc.started_at else None,
                "completed_at": tc.completed_at.isoformat()
                if tc.completed_at
                else None,
                "duration_ms": tc.duration_ms,
            }
            for tc in tool_calls
        ]

    def _convert_tool_calls_to_audit(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolAudit]:
        """Convert ToolCall objects to ToolAudit format for API responses"""
        tool_stats = {}

        for tc in tool_calls:
            if tc.tool not in tool_stats:
                tool_stats[tc.tool] = {"count": 0, "total_ms": 0.0}

            tool_stats[tc.tool]["count"] += 1
            if tc.duration_ms:
                tool_stats[tc.tool]["total_ms"] += tc.duration_ms

        return [
            ToolAudit(name=tool_name, count=stats["count"], total_ms=stats["total_ms"])
            for tool_name, stats in tool_stats.items()
        ]
