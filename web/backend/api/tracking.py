"""
Tracking API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class TrackResponse(BaseModel):
    id: str
    position: dict
    velocity: dict
    observation_count: int
    status: str
    covariance_trace: float


class TrackerConfig(BaseModel):
    motion_model: str = "constant_velocity"
    process_noise: float = 0.1
    measurement_noise_scale: float = 1.0
    coast_max_steps: int = 10
    gate_threshold: float = 9.21


# Mock tracks storage
TRACKS_DB = {}


@router.get("", response_model=list[dict])
async def list_tracks():
    """List all tracks."""
    return list(TRACKS_DB.values())


@router.get("/{track_id}")
async def get_track(track_id: str):
    """Get track details."""
    if track_id not in TRACKS_DB:
        raise HTTPException(status_code=404, detail="Track not found")
    return TRACKS_DB[track_id]


@router.post("/config")
async def set_tracker_config(config: dict):
    """Set tracker configuration."""
    # In real app, update tracker configuration
    return {"message": "Tracker configuration updated"}


@router.post("/reset")
async def reset_tracker():
    """Reset tracker."""
    global TRACKS_DB
    TRACKS_DB = {}
    return {"message": "Tracker reset"}


@router.get("/stats/summary")
async def get_tracking_stats():
    """Get tracking statistics."""
    active = sum(1 for t in TRACKS_DB.values() if t.get("status") == "active")
    coasting = sum(1 for t in TRACKS_DB.values() if t.get("status") == "coasting")
    lost = sum(1 for t in TRACKS_DB.values() if t.get("status") == "lost")

    total_obs = sum(t.get("obs_count", 0) for t in TRACKS_DB.values())
    total_cov = sum(t.get("cov_trace", 0) for t in TRACKS_DB.values())

    return {
        "total_tracks": len(TRACKS_DB),
        "active_tracks": active,
        "coasting_tracks": coasting,
        "lost_tracks": lost,
        "total_observations": total_obs,
        "avg_observations_per_track": total_obs / max(len(TRACKS_DB), 1),
        "avg_covariance_trace": total_cov / max(len(TRACKS_DB), 1),
    }
