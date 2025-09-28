from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_redis_client

router = APIRouter()


@router.get("/healthz")
async def health_check(
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    """Health check endpoint"""
    # TODO: Implement health check for database and Redis
    return {"status": "healthy", "service": "atlas-travel-advisor"}


@router.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    # TODO: Implement metrics collection
    return {
        "uptime": "0s",
        "requests_total": 0,
        "active_connections": 0,
        "database_connections": 0
    }
