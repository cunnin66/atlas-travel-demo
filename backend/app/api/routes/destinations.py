from typing import List

from app.api.deps import get_current_user, get_db
from app.models.destination import Destination
from app.models.user import User
from app.schemas.destination import (
    DestinationCreate,
    DestinationResponse,
    DestinationUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("", response_model=List[DestinationResponse])
async def get_destinations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all destinations"""
    org_id = current_user.org_id
    return (
        db.query(Destination)
        .filter(Destination.org_id == org_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("", response_model=DestinationResponse)
async def create_destination(
    destination_data: DestinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new destination"""
    org_id = current_user.org_id
    destination = Destination(
        name=destination_data.name,
        description=destination_data.description,
        org_id=org_id,
    )
    db.add(destination)
    db.commit()
    db.refresh(destination)
    return destination


@router.get("/{destination_id}", response_model=DestinationResponse)
async def get_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific destination"""
    org_id = current_user.org_id
    destination = (
        db.query(Destination)
        .filter(Destination.org_id == org_id, Destination.id == destination_id)
        .first()
    )
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found"
        )
    return destination


@router.put("/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: int,
    destination_data: DestinationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a destination"""
    org_id = current_user.org_id
    destination = (
        db.query(Destination)
        .filter(Destination.org_id == org_id, Destination.id == destination_id)
        .first()
    )
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found"
        )
    # Update all fields present in the request that exist on the model
    update_data = destination_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(destination, field):
            setattr(destination, field, value)

    db.commit()
    db.refresh(destination)
    return destination


@router.delete("/{destination_id}")
async def delete_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a destination"""
    # TODO: Implement delete destination
    pass
