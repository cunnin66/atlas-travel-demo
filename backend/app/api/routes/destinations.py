from typing import List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.destination import (
    DestinationCreate,
    DestinationResponse,
    DestinationUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=List[DestinationResponse])
async def get_destinations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all destinations"""
    # TODO: Implement get destinations
    pass


@router.post("/", response_model=DestinationResponse)
async def create_destination(
    destination_data: DestinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new destination"""
    # TODO: Implement create destination
    pass


@router.get("/{destination_id}", response_model=DestinationResponse)
async def get_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific destination"""
    # TODO: Implement get destination by ID
    pass


@router.put("/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: int,
    destination_data: DestinationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a destination"""
    # TODO: Implement update destination
    pass


@router.delete("/{destination_id}")
async def delete_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a destination"""
    # TODO: Implement delete destination
    pass
