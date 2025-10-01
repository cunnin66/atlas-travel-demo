# EXECUTOR NODE
# Execute plan steps with tool calls, support parallel execution where applicable

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Union

from app.nodes.base import BaseNode
from app.nodes.flights import AmadeusFlightTool, FlightToolFixture
from app.schemas.agent import AgentState, PlanStep, ToolCall
from langchain_core.messages import AIMessage, BaseMessage

TOOL_CONFIG = {
    "search_flights": {type: "fixture"},  # amadeus, fixture
}


class ExecutorNode(BaseNode):
    async def __call__(self, state: AgentState):
        print(f"---EXECUTOR NODE ({state['session_id']})---")
        try:
            plan = state["plan"]
            tool_calls = state.get("tool_calls", [])

            if len(plan) == 0:
                # No more steps to execute, proceed to synthesizer
                return {"messages": []}

            # Find steps that can be executed (no unresolved dependencies)
            executable_steps = self._find_executable_steps(plan, tool_calls)

            if not executable_steps:
                # No executable steps found - this shouldn't happen with a valid plan
                print("WARNING: No executable steps found in plan")
                return {"messages": [], "plan": []}

            print(
                f"Executing {len(executable_steps)} steps in parallel: {[s['id'] for s in executable_steps]}"
            )

            # Execute steps (in parallel if possible)
            messages, new_tool_calls = await self._execute_steps(executable_steps)

            # Remove executed steps from plan and add new tool calls
            executed_step_ids = [step["id"] for step in executable_steps]
            remaining_plan = [
                step for step in plan if step["id"] not in executed_step_ids
            ]
            updated_tool_calls = tool_calls + new_tool_calls

            return {
                "messages": messages,
                "plan": remaining_plan,
                "tool_calls": updated_tool_calls,
            }
        except Exception as e:
            print(f"ERROR IN EXECUTOR: {e}")
            return {"messages": [], "plan": [], "tool_calls": []}

    def _find_executable_steps(
        self, plan: List[PlanStep], tool_calls: List[ToolCall]
    ) -> List[PlanStep]:
        """Find steps that can be executed (all dependencies satisfied)"""
        executable_steps = []
        completed_step_ids = set(
            tc.id for tc in tool_calls if tc.completed_at is not None
        )

        for step in plan:
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(
                dep_id in completed_step_ids for dep_id in step["depends_on"]
            )

            if dependencies_satisfied:
                executable_steps.append(step)

        return executable_steps

    async def _execute_steps(
        self, steps: List[PlanStep]
    ) -> tuple[List[BaseMessage], List[ToolCall]]:
        """Execute the given steps in parallel and return tool messages and tool call records"""
        messages = []
        tool_call_records = []

        # Create tool calls for OpenAI format
        tool_calls_data = []
        tool_messages = []

        # Create tool call records for internal tracking
        tool_calls = []
        for step in steps:
            tool_call = ToolCall(
                id=step["id"],
                tool=step["tool"],
                args=step["args"],
                started_at=datetime.now(),
            )
            tool_calls.append(tool_call)

            # Create tool call data for OpenAI format
            tool_call_data = {
                "id": step["id"],
                "type": "function",
                "function": {
                    "name": step["tool"],
                    "arguments": json.dumps(step["args"]),  # Convert to JSON string
                },
            }
            tool_calls_data.append(tool_call_data)

        # Execute all steps in parallel
        async def execute_step_with_timing(step: PlanStep, tool_call: ToolCall):
            start_time = time.time()
            try:
                result = await self._execute_single_step(step)
                end_time = time.time()

                # Update tool call record with success
                tool_call.result = str(result)
                tool_call.completed_at = datetime.now()
                tool_call.duration_ms = (end_time - start_time) * 1000

                tool_message = AIMessage(
                    content=str(result),
                )
                print(
                    f"Executed step {step['id']} with tool {step['tool']} in {tool_call.duration_ms:.2f}ms"
                )
                return tool_message, None

            except Exception as e:
                end_time = time.time()

                # Update tool call record with error
                tool_call.error = str(e)
                tool_call.completed_at = datetime.now()
                tool_call.duration_ms = (end_time - start_time) * 1000

                error_message = AIMessage(
                    content=f"Error executing {step['tool']}: {str(e)}",
                    tool_call_id=step["id"],
                    name=step["tool"],
                )
                print(f"Error executing step {step['id']}: {e}")
                return None, error_message

        # Run all steps in parallel
        tasks = [
            execute_step_with_timing(step, tool_call)
            for step, tool_call in zip(steps, tool_calls)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                # Handle any unexpected exceptions from asyncio.gather
                error_message = AIMessage(
                    content=f"Unexpected error: {str(result)}",
                )
                messages.append(error_message)
            else:
                tool_message, error_message = result
                if tool_message:
                    tool_messages.append(tool_message)
                if error_message:
                    messages.append(error_message)

        tool_call_records.extend(tool_calls)

        # Create an AIMessage with tool_calls first, then add tool messages
        if tool_calls_data:
            ai_message = AIMessage(
                content=f"Executed tools {json.dumps(tool_calls_data)}",
                # tool_calls=tool_calls_data
            )
            messages.append(ai_message)
            # messages.extend(tool_messages)

        return messages, tool_call_records

    async def _execute_single_step(self, step: PlanStep) -> Any:
        """Execute a single step based on its tool type"""
        tool_name = step["tool"]
        args = step["args"]

        if tool_name == "weather":
            return await self._execute_weather_tool(args)
        elif tool_name == "search_flights":
            return await self._execute_flights_tool(args)
        elif tool_name == "agent":
            return await self._execute_agent_tool(args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _execute_weather_tool(self, args: Dict[str, Any]) -> str:
        """Execute weather tool - placeholder implementation"""
        location = args.get("location", "Unknown")
        days = args.get("days", 1)

        # TODO: Implement actual weather API call
        # Simulate async API call with a small delay
        await asyncio.sleep(0.1)
        return f"Weather forecast for {location} for {days} days: Partly cloudy, 20-25°C. Good weather for travel activities."

    async def _execute_flights_tool(self, args: Dict[str, Any]) -> str:
        """Execute flights search tool - placeholder implementation"""
        origin = args.get("origin", "Unknown")
        destination = args.get("destination", "Unknown")
        departure_date = args.get("departure_date", "Unknown")

        if TOOL_CONFIG.get("search_flights", {}).get("type") == "amadeus":
            return await AmadeusFlightTool().execute(
                origin, destination, departure_date
            )
        else:
            return await FlightToolFixture().execute(
                origin, destination, departure_date
            )

    async def _execute_agent_tool(self, args: Dict[str, Any]) -> str:
        """Execute agent tool - placeholder implementation"""
        prompt = args.get("prompt", "")

        # TODO: Implement actual agent call for complex reasoning
        # Simulate async API call with a small delay
        await asyncio.sleep(0.1)
        return f"Agent analysis: {prompt} - This requires detailed planning based on the gathered information."
