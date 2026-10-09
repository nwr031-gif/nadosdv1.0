"""
Scenarios API endpoints.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from pathlib import Path

router = APIRouter()

class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    duration_seconds: float
    timestep_seconds: float
    random_seed: int
    coordinate_system: str
    objects_count: int
    sensors_count: int

class ScenarioListResponse(BaseModel):
    scenarios: List[ScenarioResponse]
    total: int

def _scenarios_dir(request: Request) -> Path:
    return Path(getattr(request.app.state, "scenarios_dir", "scenarios"))

@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List available scenarios."""
    scenarios_dir = _scenarios_dir(request)
    scenarios = []

    if scenarios_dir.exists():
        for file in sorted(scenarios_dir.glob("*.json")):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                scenarios.append(ScenarioResponse(
                    id=data.get("scenario_id", file.stem),
                    name=data.get("name", file.stem),
                    description=data.get("description", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    timestep_seconds=data.get("timestep_seconds", 0),
                    random_seed=data.get("random_seed", 0),
                    coordinate_system=data.get("coordinate_system", "ENU"),
                    objects_count=len(data.get("virtual_objects", [])),
                    sensors_count=len(data.get("simulated_sensors", []))
                ))
            except Exception:
                continue

    total = len(scenarios)
    return ScenarioListResponse(
        scenarios=scenarios[offset:offset+limit],
        total=total
    )

@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str, request: Request):
    """Get scenario details."""
    file_path = _scenarios_dir(request) / f"{scenario_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {str(e)}")

@router.post("")
async def create_scenario(scenario: dict, request: Request):
    """Create a new scenario."""
    scenario_id = scenario.get("scenario_id")
    if not scenario_id:
        raise HTTPException(status_code=400, detail="scenario_id is required")

    scenarios_dir = _scenarios_dir(request)
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    file_path = scenarios_dir / f"{scenario_id}.json"
    if file_path.exists():
        raise HTTPException(status_code=409, detail="Scenario already exists")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False)
        return {"message": "Scenario created successfully", "id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")

@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, scenario: dict, request: Request):
    """Update an existing scenario."""
    file_path = _scenarios_dir(request) / f"{scenario_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False)
        return {"message": "Scenario updated successfully", "id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scenario: {str(e)}")

@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str, request: Request):
    """Delete a scenario."""
    file_path = _scenarios_dir(request) / f"{scenario_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        file_path.unlink()
        return {"message": "Scenario deleted successfully", "id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scenario: {str(e)}")

@router.post("/{scenario_id}/validate")
async def validate_scenario(scenario_id: str, request: Request):
    """Validate a scenario."""
    file_path = _scenarios_dir(request) / f"{scenario_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = []

        required_fields = ["scenario_id", "schema_version", "name", "duration_seconds",
                          "timestep_seconds", "random_seed", "coordinate_system"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if data.get("duration_seconds", 0) <= 0:
            errors.append("duration_seconds must be positive")

        if data.get("timestep_seconds", 0) <= 0:
            errors.append("timestep_seconds must be positive")

        if data.get("random_seed", -1) < 0:
            errors.append("random_seed must be non-negative")

        object_ids = set()
        for obj in data.get("virtual_objects", []):
            oid = obj.get("object_id")
            if not oid:
                errors.append("Object missing object_id")
            elif oid in object_ids:
                errors.append(f"Duplicate object_id: {oid}")
            object_ids.add(oid)

        sensor_ids = set()
        for sensor in data.get("simulated_sensors", []):
            sid = sensor.get("sensor_id")
            if not sid:
                errors.append("Sensor missing sensor_id")
            elif sid in sensor_ids:
                errors.append(f"Duplicate sensor_id: {sid}")
            sensor_ids.add(sid)

        if errors:
            return {"valid": False, "errors": errors}
        else:
            return {"valid": True, "message": "Scenario is valid"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")