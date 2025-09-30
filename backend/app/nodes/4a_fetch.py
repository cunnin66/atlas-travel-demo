# TOOL EXECUTOR
# executes calls with timeouts, retries (1 with jitter), caching/dedup by input hash, records timing

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState


class ToolExecutorNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---TOOL EXECUTOR NODE (${state['session_id']})---")
        # Run tools in parallel
        import asyncio

        async def run_tool_call(tool_call):
            return await self.tool_executor.invoke(tool_call)

        async def run_all_tool_calls():
            tasks = [run_tool_call(tool_call) for tool_call in state["plan"]]
            return await asyncio.gather(*tasks)

        responses = asyncio.run(run_all_tool_calls())
        return {}
