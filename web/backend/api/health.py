"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import time

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    checks: Dict[str, Any]

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        checks={
            "database": "healthy",
            "simulation": "healthy",
            "api": "healthy"
        }
    )

@router.get("/health/live")
async def liveness():
    """Liveness probe."""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness():
    """Readiness probe."""
    return {"status": "ready"}