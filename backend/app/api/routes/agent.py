import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.agent import (
    Activity,
    Citation,
    DayPlan,
    Itinerary,
    PlanRequest,
    PlanResponse,
    StatusUpdate,
    ToolAudit,
)
from app.services.agent_service import AgentService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()

# In-memory storage for fake plans (in production, this would be in a database)
fake_plans_storage: Dict[str, PlanResponse] = {}


class FakeStreamRequest(BaseModel):
    """Request schema for fake streaming endpoint"""

    destination_id: int
    prompt: str
    plan_id: Optional[str] = None  # If provided, this is an edit request


def create_hardcoded_plan_response(query: str, is_edit: bool = False) -> PlanResponse:
    """Create a hardcoded PlanResponse for testing"""

    # Sample activities
    activities_day1 = [
        Activity(
            name="Morning Coffee & Planning",
            description="Start the day with local coffee and review the itinerary",
            duration=60,
            cost=15.0,
            location="Local Café",
        ),
        Activity(
            name="City Walking Tour",
            description="Explore the historic downtown area with a guided tour",
            duration=180,
            cost=45.0,
            location="Downtown Historic District",
        ),
        Activity(
            name="Lunch at Local Restaurant",
            description="Try authentic local cuisine at a recommended restaurant",
            duration=90,
            cost=35.0,
            location="Traditional Restaurant",
        ),
        Activity(
            name="Museum Visit",
            description="Visit the main city museum to learn about local history",
            duration=120,
            cost=20.0,
            location="City Museum",
        ),
    ]

    activities_day2 = [
        Activity(
            name="Nature Hike",
            description="Morning hike in the nearby national park",
            duration=240,
            cost=0.0,
            location="National Park Trail",
        ),
        Activity(
            name="Picnic Lunch",
            description="Enjoy a packed lunch with scenic mountain views",
            duration=60,
            cost=25.0,
            location="Mountain Viewpoint",
        ),
        Activity(
            name="Local Market Shopping",
            description="Browse local crafts and souvenirs at the artisan market",
            duration=120,
            cost=50.0,
            location="Artisan Market",
        ),
    ]

    # Modify activities slightly if this is an edit
    if is_edit:
        activities_day1[
            1
        ].description = "EDITED: Enhanced walking tour with additional historical sites"
        activities_day2.append(
            Activity(
                name="Sunset Photography",
                description="NEW: Capture beautiful sunset photos from the best viewpoint",
                duration=90,
                cost=0.0,
                location="Sunset Viewpoint",
            )
        )

    # Create day plans
    day1 = DayPlan(
        date="2024-03-15",
        activities=activities_day1,
        total_cost=115.0 if not is_edit else 115.0,
    )

    day2 = DayPlan(
        date="2024-03-16",
        activities=activities_day2,
        total_cost=75.0 if not is_edit else 75.0,
    )

    # Create itinerary
    itinerary = Itinerary(
        total_cost_usd=190.0 if not is_edit else 190.0, days=[day1, day2]
    )

    # Create citations
    citations = [
        Citation(
            title="Local Tourism Guide", source="manual", ref="tourism_guide_2024"
        ),
        Citation(
            title="Restaurant Reviews Database", source="tool", ref="reviews_tool#123"
        ),
    ]

    # Create tool audit
    tools_used = [
        ToolAudit(name="weather_api", count=2, total_ms=450.0),
        ToolAudit(name="maps_api", count=5, total_ms=1200.0),
        ToolAudit(name="reviews_api", count=3, total_ms=800.0),
    ]

    decisions = [
        "Selected morning activities to avoid afternoon crowds",
        "Chose restaurants based on dietary preferences",
        "Included outdoor activities based on weather forecast",
    ]

    if is_edit:
        decisions.append("EDIT: Added photography session based on user request")
        decisions.append("EDIT: Enhanced walking tour with more historical content")

    # Prepare strings with newlines outside f-string expressions
    recent_changes_section = """## Recent Changes
- Enhanced walking tour with additional historical sites
- Added sunset photography session
- Updated activity descriptions"""

    evening_activity = "- **Evening**: Sunset photography session" if is_edit else ""

    answer_markdown = f"""
# Travel Plan {"(Updated)" if is_edit else ""}

Based on your request: "{query}"

## Overview
{"This is an updated version of your travel plan with the requested modifications." if is_edit else "Here's a comprehensive 2-day travel plan tailored to your preferences."}

## Day 1 - Cultural Exploration
- **Morning**: Start with local coffee culture
- **Midday**: {"Enhanced historical walking tour" if is_edit else "Guided walking tour"}
- **Afternoon**: Authentic dining experience
- **Evening**: Cultural enrichment at the museum

## Day 2 - Nature & Local Life
- **Morning**: Outdoor adventure in nature
- **Midday**: Scenic lunch break
- **Afternoon**: Local market exploration
{evening_activity}

## Key Highlights
- Total budget: $190 USD
- Mix of cultural and outdoor activities
- Local cuisine experiences
- {"Updated with enhanced historical content and photography" if is_edit else "Balanced schedule with rest periods"}

{recent_changes_section if is_edit else ""}
"""

    return PlanResponse(
        query=query,
        answer_markdown=answer_markdown.strip(),
        itinerary=itinerary,
        citations=citations,
        tools_used=tools_used,
        decisions=decisions,
        status="completed",
        created_at=datetime.now(),
    )


@router.post("/plan", response_model=PlanResponse)
async def create_travel_plan(
    plan_request: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a travel plan using AI agent (batch mode)"""
    agent_service = AgentService(current_user, db)
    plan = await agent_service.create_travel_plan(plan_request)
    return plan


@router.post("/stream")
async def stream_agent_response(
    request: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream AI agent responses via Server-Sent Events"""
    agent_service = AgentService(current_user, db)

    async def stream_generator():
        async for chunk in agent_service.stream_agent_response(request):
            yield chunk

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@router.post("/fakeStream")
async def fake_stream_agent_response(
    request: FakeStreamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fake streaming endpoint that mimics AI agent behavior with support for plan editing"""

    async def fake_stream_generator():
        # Determine if this is an edit request
        is_edit = request.plan_id is not None
        existing_plan = None

        if is_edit:
            existing_plan = fake_plans_storage.get(request.plan_id)
            if not existing_plan:
                # Send error if plan_id doesn't exist
                error_update = StatusUpdate(
                    type="error", content=f"Plan with ID {request.plan_id} not found"
                )
                yield f"data: {error_update.model_dump_json()}\n\n"
                return

        # Define different status messages for initial vs edit requests
        if is_edit:
            status_messages = [
                "🔄 Loading existing travel plan...",
                "📝 Analyzing your modification request...",
                "🔍 Identifying changes to make...",
                "✨ Updating activities and recommendations...",
                "🎯 Finalizing your updated travel plan...",
            ]
        else:
            status_messages = [
                "🚀 Starting travel plan creation...",
                "🌍 Analyzing destination preferences...",
                "🔍 Researching activities and attractions...",
                "📅 Building your personalized itinerary...",
                "✅ Finalizing your travel plan...",
            ]

        # Send 5 status updates, one every 2 seconds
        for i, message in enumerate(status_messages):
            status_update = StatusUpdate(type="status", content=message)
            yield f"data: {status_update.model_dump_json()}\n\n"

            # Don't wait after the last message
            if i < len(status_messages) - 1:
                await asyncio.sleep(2)

        # Generate the final plan response
        plan_response = create_hardcoded_plan_response(request.prompt, is_edit=is_edit)

        # Store the plan with a simple ID (in production, use proper UUID)
        plan_id = request.plan_id if is_edit else f"plan_{len(fake_plans_storage) + 1}"
        fake_plans_storage[plan_id] = plan_response

        # Create final response with plan_id included
        final_response = {
            "type": "plan_complete",
            "plan_id": plan_id,
            "is_edit": is_edit,
            "plan": plan_response.model_dump(
                mode="json"
            ),  # Use JSON mode for proper datetime serialization
        }

        yield f"data: {json.dumps(final_response, default=str)}\n\n"

        # Send completion signal
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        fake_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
