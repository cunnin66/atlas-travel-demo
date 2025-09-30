from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.agent import PlanRequest, PlanResponse
from app.services.agent_service import AgentService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

router = APIRouter()


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
