# from typing import Any, Dict, Optional, List
# from pydantic import BaseModel
# from langchain_core.tools import Tool

# from app.services.agent_service import tool_registry
# from app.agents.weather import weather_tool
# from app.agents.flights import flights_tool


# # --- Tool Registry System ---


# class ToolRegistry:
#     """Registry for managing agent tools"""

#     def __init__(self):
#         self._tools: Dict[str, BaseTool] = {}

#     def register(self, tool: BaseTool):
#         """Register a tool in the registry"""
#         self._tools[tool.name] = tool

#     def get_tool(self, name: str) -> Optional[BaseTool]:
#         """Get a tool by name"""
#         return self._tools.get(name)

#     def get_all_tools(self) -> Dict[str, BaseTool]:
#         """Get all registered tools"""
#         return self._tools.copy()

#     def create_langchain_tools(self) -> List[Tool]:
#         """Create LangChain Tool objects from registered tools"""
#         return [
#             Tool(
#                 name=tool.name,
#                 description=tool.description,
#                 func=self._create_tool_wrapper(tool),
#                 args_schema=tool.get_args_schema(),
#             )
#             for tool in self._tools.values()
#         ]

#     def _create_tool_wrapper(self, tool: BaseTool):
#         """Create a wrapper function for async tool execution"""
#         async def wrapper(**kwargs):
#             return await tool.execute(**kwargs)
#         return wrapper


# def register_all_tools():
#     """Register all available tools with the global registry"""
#     tool_registry.register(weather_tool)
#     tool_registry.register(flights_tool)

#     print(f"Registered {len(tool_registry.get_all_tools())} agent tools:")
#     for tool_name in tool_registry.get_all_tools().keys():
#         print(f"  - {tool_name}")


# # Global tool registry instance
# tool_registry = ToolRegistry()
# register_all_tools()
