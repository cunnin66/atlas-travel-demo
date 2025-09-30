# LangGraph Agent System

This directory contains the extensible agent system built with LangGraph for the Atlas Travel Demo.

## Architecture Overview

### Core Components

1. **Tool Registry System** (`agent_service.py`)
   - `BaseTool`: Abstract base class for all agent tools
   - `ToolRegistry`: Manages registration and creation of tools
   - `tool_registry`: Global registry instance

2. **Agent State** (`agent_service.py`)
   - Enhanced state management for travel planning context
   - Tracks messages, tool calls, citations, and node events
   - Maintains user context and session information

3. **LangGraph Workflow** (`agent_service.py`)
   - Dynamic workflow creation based on registered tools
   - Streaming and batch execution modes
   - Proper error handling and state management

4. **Agent Tools** (individual tool files)
   - `WeatherTool`: Get weather forecasts for locations
   - `FlightTool`: Search for flights between destinations
   - Extensible system for adding new tools

## Adding New Tools

To add a new tool to the system:

1. **Create a new tool file** (e.g., `hotels.py`):

```python
from typing import Any, Dict
from pydantic import BaseModel, Field
from app.services.agent_service import BaseTool

class HotelSearchSchema(BaseModel):
    location: str = Field(description="Location to search for hotels")
    checkin_date: str = Field(description="Check-in date (YYYY-MM-DD)")
    checkout_date: str = Field(description="Check-out date (YYYY-MM-DD)")

class HotelTool(BaseTool):
    name: str = "search_hotels"
    description: str = "Search for hotels in a specific location"

    def get_args_schema(self) -> BaseModel:
        return HotelSearchSchema

    async def execute(self, location: str, checkin_date: str, checkout_date: str) -> Dict[str, Any]:
        # Implement hotel search logic
        return {"success": True, "data": {...}}

# Create tool instance
hotel_tool = HotelTool()
```

2. **Register the tool** in `__init__.py`:

```python
from app.agents.hotels import hotel_tool

def register_all_tools():
    tool_registry.register(weather_tool)
    tool_registry.register(flights_tool)
    tool_registry.register(hotel_tool)  # Add new tool
```

3. **The tool is automatically available** to the agent workflow!

## API Endpoints

### Batch Mode: `/api/agent/plan`
- Creates a complete travel plan in one request
- Returns structured `PlanResponse` with itinerary
- Suitable for simple integrations

### Streaming Mode: `/api/agent/stream`
- Streams real-time updates via Server-Sent Events
- Provides node execution events, tool calls, and messages
- Suitable for interactive UIs

## System Prompts & Agent Instructions

The system includes a comprehensive system prompt that instructs the LLM on how to create travel itineraries:

### Core Instructions
The agent is instructed to:
1. **Analyze the Request** - Extract destination, duration, dates, budget, interests
2. **Gather Information** - Use weather and flight tools strategically
3. **Create Detailed Itinerary** - Structure day-by-day with specific activities
4. **Provide Comprehensive Information** - Include practical details, costs, tips

### Dynamic Tool Integration
The system prompt automatically includes all registered tools:
```python
# Tools are dynamically listed in the system prompt
"You have access to the following tools:
- get_weather: Get weather forecasts for destinations
- search_flights: Find flights between locations"
```

### User Personalization
The system includes user context from previous trips:
```python
# Example personalized context
"## User Context
- Previous trips: Paris, Tokyo, London
- Travel preferences: Cultural experiences, local cuisine
- Typical budget range: $2000-3000"
```

### Response Structure
The agent is instructed to format responses with:
- **Travel Overview** with destination highlights and budget
- **Daily Itinerary** with morning/afternoon/evening activities
- **Practical Information** with weather, transport, and local tips

## Usage Examples

### Batch Request
```python
request = PlanRequest(
    destination_id=1,
    prompt="Plan a 5-day trip to Paris with weather and flight information"
)
response = await agent_service.create_travel_plan(request, user)

# The agent will:
# 1. Receive comprehensive system instructions
# 2. Use weather tool to check Paris conditions
# 3. Use flight tool to find transportation options
# 4. Create structured itinerary with parsed activities
# 5. Return PlanResponse with structured Itinerary object
```

### Streaming Request
```python
async for chunk in agent_service.stream_agent_response(request, user):
    # Process streaming updates
    data = json.loads(chunk.replace("data: ", ""))
    if data["type"] == "message":
        print(f"Agent: {data['content']}")
    elif data["type"] == "tool_call":
        print(f"Using tool: {data['tool_name']}")
```

### Example Agent Flow
1. **System Message**: "You are Atlas, an expert travel planning assistant..."
2. **User Message**: "Plan a 5-day trip to Paris for $2000"
3. **Agent Reasoning**: Analyzes request, identifies need for weather/flights
4. **Tool Calls**: `get_weather(location="Paris", days=5)`, `search_flights(...)`
5. **Final Response**: Comprehensive itinerary with structured data

## State Management

The agent maintains rich state throughout execution:

- **Messages**: Conversation history with the user
- **Tool Calls**: Track which tools were used and when
- **Citations**: Source attribution for information
- **Node Events**: Detailed execution timeline
- **Context**: User, session, and request information

## Database Integration

Agent runs are automatically tracked in the database:

- **AgentRun** model stores execution metadata
- **Status tracking**: pending → running → completed/failed
- **Response storage**: Full agent responses are persisted
- **Session management**: Multiple runs can be grouped by session

## Error Handling

The system includes comprehensive error handling:

- **Tool failures**: Individual tool errors don't crash the workflow
- **Workflow errors**: Graceful degradation with error reporting
- **Database errors**: Proper transaction management
- **Streaming errors**: Error events sent to client

## Configuration

Key configuration options:

- **Model**: Currently uses `gpt-4o` (configurable in `create_agent_workflow`)
- **Temperature**: Set to 0 for consistent responses
- **Tool binding**: Automatic based on registered tools
- **Streaming**: Real-time updates with proper SSE headers

## Testing

Use the provided test script to verify setup:

```bash
python test_agent_setup.py
```

This tests:
- Tool registry functionality
- Agent workflow creation
- Schema validation
- Basic integration

## Future Enhancements

Potential improvements:

1. **Tool Categories**: Group tools by functionality
2. **Conditional Tool Loading**: Load tools based on request type
3. **Tool Caching**: Cache tool results for efficiency
4. **Advanced Routing**: Smart tool selection based on context
5. **Tool Composition**: Chain multiple tools automatically
6. **Performance Monitoring**: Track tool execution times
7. **A/B Testing**: Compare different tool configurations
