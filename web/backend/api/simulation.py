"""
Simulation API endpoints.
"""

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class SimulationStatusResponse(BaseModel):
    status: str
    current_time: float
    duration: float
    progress: float
    speed: float
    objects_count: int
    sensors_count: int
    tracks_count: int


class SimulationControlResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None


class LoadScenarioRequest(BaseModel):
    scenario_id: str


class SpeedRequest(BaseModel):
    speed: float


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status(request: Request):
    """Get current simulation status."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        return SimulationStatusResponse(
            status="idle",
            current_time=0.0,
            duration=0.0,
            progress=0.0,
            speed=1.0,
            objects_count=0,
            sensors_count=0,
            tracks_count=0,
        )

    engine = nados_app.engine
    return SimulationStatusResponse(
        status=engine.state.value,
        current_time=engine.current_time,
        duration=engine.clock.time.duration,
        progress=engine.progress,
        speed=engine.clock.time.speed_multiplier,
        objects_count=len(engine._object_simulators),
        sensors_count=len(engine._sensor_simulators),
        tracks_count=len(getattr(nados_app, "tracker", None) and nados_app.tracker.manager.tracks or {}),
    )


@router.get("/objects")
async def get_objects(request: Request):
    """Get all simulated objects."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        return {"objects": {}}

    objects = {}
    for obj_id, obj_sim in nados_app.engine._object_simulators.items():
        state = obj_sim.state
        trail = [{"x": s.position.x, "y": s.position.y, "z": s.position.z} for s in obj_sim.get_trajectory()[-100:]]
        objects[obj_id] = {
            "id": obj_id,
            "type": obj_sim.virtual_object.object_type,
            "position": {"x": state.position.x, "y": state.position.y, "z": state.position.z},
            "velocity": {"x": state.velocity.x, "y": state.velocity.y, "z": state.velocity.z},
            "acceleration": {"x": state.acceleration.x, "y": state.acceleration.y, "z": state.acceleration.z},
            "speed": (state.velocity.x**2 + state.velocity.y**2 + state.velocity.z**2) ** 0.5,
            "heading": 0.0,
            "trail": trail,
        }

    return {"objects": objects}


@router.get("/sensors")
async def get_sensors(request: Request):
    """Get all sensors."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        return {"sensors": {}}

    sensors = {}
    for sensor_id, sensor_sim in nados_app.engine._sensor_simulators.items():
        sensors[sensor_id] = {
            "id": sensor_id,
            "type": sensor_sim.sensor_def.sensor_type,
            "position": {
                "x": sensor_sim.sensor_def.simulated_position.x,
                "y": sensor_sim.sensor_def.simulated_position.y,
                "z": sensor_sim.sensor_def.simulated_position.z,
            },
            "sampling_interval": sensor_sim.sensor_def.sampling_interval,
            "status": "active" if sensor_sim._available else "inactive",
        }

    return {"sensors": sensors}


@router.get("/tracks")
async def get_tracks(request: Request):
    """Get all tracks."""
    nados_app = getattr(request.app.state, "nados_app", None)

    tracker = getattr(nados_app, "tracker", None) if nados_app else None
    if not tracker:
        return {"tracks": {}}

    tracks = {}
    for track_id, track in tracker.manager.tracks.items():
        estimate = track.get_estimate()
        tracks[track_id] = {
            "id": track_id,
            "position": {
                "x": estimate.estimated_position.x,
                "y": estimate.estimated_position.y,
                "z": estimate.estimated_position.z,
            },
            "velocity": {
                "x": estimate.estimated_velocity.x,
                "y": estimate.estimated_velocity.y,
                "z": estimate.estimated_velocity.z,
            },
            "observation_count": estimate.observation_count,
            "status": estimate.tracking_status,
            "covariance_trace": sum(estimate.covariance_or_uncertainty.data[i][i] for i in range(3)),
        }

    return {"tracks": tracks}


@router.post("/start", response_model=SimulationControlResponse)
async def start_simulation(request: Request):
    """Start the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No scenario loaded")

    try:
        if nados_app.engine.state.value == "running":
            return SimulationControlResponse(success=False, message="Simulation already running")

        nados_app.engine.start()
        return SimulationControlResponse(success=True, message="Simulation started", data={"status": "running"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")


@router.post("/pause", response_model=SimulationControlResponse)
async def pause_simulation(request: Request):
    """Pause the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation running")

    try:
        nados_app.engine.pause()
        return SimulationControlResponse(success=True, message="Simulation paused", data={"status": "paused"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause: {str(e)}")


@router.post("/resume", response_model=SimulationControlResponse)
async def resume_simulation(request: Request):
    """Resume the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation running")

    try:
        nados_app.engine.start()  # Resumes
        return SimulationControlResponse(success=True, message="Simulation resumed", data={"status": "running"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume: {str(e)}")


@router.post("/stop", response_model=SimulationControlResponse)
async def stop_simulation(request: Request):
    """Stop the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation running")

    try:
        nados_app.engine.stop()
        nados_app._save_simulation_results()
        return SimulationControlResponse(success=True, message="Simulation stopped", data={"status": "stopped"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")


@router.post("/reset", response_model=SimulationControlResponse)
async def reset_simulation(request: Request):
    """Reset the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation to reset")

    try:
        nados_app.engine.reset()
        return SimulationControlResponse(success=True, message="Simulation reset", data={"status": "idle"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset: {str(e)}")


@router.post("/speed", response_model=SimulationControlResponse)
async def set_speed(request: Request, speed_req: SpeedRequest):
    """Set simulation speed."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation running")

    if speed_req.speed <= 0:
        raise HTTPException(status_code=400, detail="Speed must be positive")

    try:
        nados_app.engine.clock.set_speed(speed_req.speed)
        return SimulationControlResponse(
            success=True, message=f"Speed set to {speed_req.speed}x", data={"speed": speed_req.speed}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set speed: {str(e)}")


@router.post("/load", response_model=SimulationControlResponse)
async def load_scenario(request: Request, load_req: LoadScenarioRequest):
    """Load a scenario into the simulation."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not load_req.scenario_id:
        raise HTTPException(status_code=400, detail="scenario_id is required")

    try:
        scenarios_dir = getattr(request.app.state, "scenarios_dir", "scenarios")
        scenario_path = os.path.join(scenarios_dir, f"{load_req.scenario_id}.json")
        success = nados_app.load_scenario(scenario_path)
        if not success:
            raise HTTPException(status_code=404, detail="Scenario not found or invalid")

        return SimulationControlResponse(
            success=True, message=f"Scenario {load_req.scenario_id} loaded", data={"scenario_id": load_req.scenario_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {str(e)}")


@router.post("/step")
async def step_simulation(request: Request):
    """Execute a single simulation step."""
    nados_app = getattr(request.app.state, "nados_app", None)

    if not nados_app or not nados_app.engine:
        raise HTTPException(status_code=400, detail="No simulation running")

    try:
        result = nados_app.engine.step()
        return {
            "success": result.success,
            "current_time": result.current_time,
            "events_count": len(result.events),
            "observations_count": len(result.observations),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")
