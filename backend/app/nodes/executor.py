# EXECUTOR NODE
# Execute plan steps with tool calls, support parallel execution where applicable

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Union

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState, PlanStep, ToolCall
from langchain_core.messages import AIMessage, BaseMessage


class ExecutorNode(BaseNode):
    def __call__(self, state: AgentState):
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
            messages, new_tool_calls = self._execute_steps(executable_steps)

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

    def _execute_steps(
        self, steps: List[PlanStep]
    ) -> tuple[List[BaseMessage], List[ToolCall]]:
        """Execute the given steps and return tool messages and tool call records"""
        messages = []
        tool_call_records = []

        # Create tool calls for OpenAI format
        tool_calls_data = []
        tool_messages = []

        for step in steps:
            # Create tool call record for internal tracking
            tool_call = ToolCall(
                id=step["id"],
                tool=step["tool"],
                args=step["args"],
                started_at=datetime.now(),
            )

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

            start_time = time.time()
            try:
                result = self._execute_single_step(step)
                end_time = time.time()

                # Update tool call record with success
                tool_call.result = str(result)
                tool_call.completed_at = datetime.now()
                tool_call.duration_ms = (end_time - start_time) * 1000

                tool_message = AIMessage(
                    content=str(result),
                )
                tool_messages.append(tool_message)
                print(
                    f"Executed step {step['id']} with tool {step['tool']} in {tool_call.duration_ms:.2f}ms"
                )

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
                messages.append(error_message)
                print(f"Error executing step {step['id']}: {e}")

            tool_call_records.append(tool_call)

        # Create an AIMessage with tool_calls first, then add tool messages
        if tool_calls_data:
            ai_message = AIMessage(
                content=f"Executed tools {json.dumps(tool_calls_data)}",
                # tool_calls=tool_calls_data
            )
            messages.append(ai_message)
            # messages.extend(tool_messages)

        return messages, tool_call_records

    def _execute_single_step(self, step: PlanStep) -> Any:
        """Execute a single step based on its tool type"""
        tool_name = step["tool"]
        args = step["args"]

        if tool_name == "weather":
            return self._execute_weather_tool(args)
        elif tool_name == "search_flights":
            return self._execute_flights_tool(args)
        elif tool_name == "agent":
            return self._execute_agent_tool(args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _execute_weather_tool(self, args: Dict[str, Any]) -> str:
        """Execute weather tool - placeholder implementation"""
        location = args.get("location", "Unknown")
        days = args.get("days", 1)

        # TODO: Implement actual weather API call
        return f"Weather forecast for {location} for {days} days: Partly cloudy, 20-25°C. Good weather for travel activities."

    def _execute_flights_tool(self, args: Dict[str, Any]) -> str:
        """Execute flights search tool - placeholder implementation"""
        origin = args.get("origin", "Unknown")
        destination = args.get("destination", "Unknown")
        departure_date = args.get("departure_date", "Unknown")
        return_date = args.get("return_date", "Unknown")
        passengers = args.get("passengers", 1)

        # TODO: Implement actual flight search API call
        return f"Flight search results for {passengers} passenger(s) from {origin} to {destination}, departing {departure_date}, returning {return_date}: Found flights starting from $650 with major airlines."

    def _execute_agent_tool(self, args: Dict[str, Any]) -> str:
        """Execute agent tool - placeholder implementation"""
        prompt = args.get("prompt", "")

        # TODO: Implement actual agent call for complex reasoning
        return f"Agent analysis: {prompt} - This requires detailed planning based on the gathered information."
