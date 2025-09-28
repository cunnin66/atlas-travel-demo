from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.agent import PlanRequest, PlanResponse
from app.models.user import User
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/qa/plan", response_model=PlanResponse)
async def create_travel_plan(
    plan_request: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a travel plan using AI agent"""
    # TODO: Implement travel plan creation
    pass


@router.websocket("/qa/stream")
async def stream_agent_response(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """Stream AI agent responses via WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            # TODO: Implement WebSocket streaming for agent responses
            data = await websocket.receive_text()
            # Process the request and stream responses
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
