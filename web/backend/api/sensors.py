"""
Sensors API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class SensorCreate(BaseModel):
    sensor_id: str
    sensor_type: str
    position: dict
    sampling_interval: float = 1.0
    noise: float = 100.0
    dropout: float = 0.0
    active: bool = True

class SensorResponse(BaseModel):
    sensor_id: str
    sensor_type: str
    position: dict
    sampling_interval: float
    noise: float
    dropout: float
    active: bool
    status: str

# In-memory storage for demo (in production, use database)
SENSORS_DB = {}

@router.get("", response_model=List[dict])
async def list_sensors():
    """List all sensors."""
    return list(SENSORS_DB.values())

@router.get("/{sensor_id}")
async def get_sensor(sensor_id: str):
    """Get sensor details."""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return SENSORS_DB[sensor_id]

@router.post("", status_code=201)
async def create_sensor(sensor: dict):
    """Create a new sensor."""
    sensor_id = sensor.get("sensor_id")
    if not sensor_id:
        raise HTTPException(status_code=400, detail="sensor_id is required")
    
    if sensor_id in SENSORS_DB:
        raise HTTPException(status_code=409, detail="Sensor already exists")
    
    sensor_data = {
        "sensor_id": sensor.get("sensor_id"),
        "sensor_type": sensor.get("sensor_type", "radar"),
        "position": sensor.get("position", {"x": 0, "y": 0, "z": 0}),
        "sampling_interval": sensor.get("sampling_interval", 1.0),
        "noise": sensor.get("noise", 100.0),
        "dropout": sensor.get("dropout", 0.0),
        "active": sensor.get("active", True),
        "status": "active" if sensor.get("active", True) else "inactive"
    }
    
    SENSORS_DB[sensor_id] = sensor_data
    return {"message": "Sensor created", "sensor": sensor_data}

@router.put("/{sensor_id}")
async def update_sensor(sensor_id: str, sensor: dict):
    """Update a sensor."""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    SENSORS_DB[sensor_id].update(sensor)
    SENSORS_DB[sensor_id]["status"] = "active" if SENSORS_DB[sensor_id].get("active", True) else "inactive"
    
    return {"message": "Sensor updated", "sensor": SENSORS_DB[sensor_id]}

@router.delete("/{sensor_id}")
async def delete_sensor(sensor_id: str):
    """Delete a sensor."""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    del SENSORS_DB[sensor_id]
    return {"message": "Sensor deleted", "id": sensor_id}

@router.post("/{sensor_id}/toggle")
async def toggle_sensor(sensor_id: str):
    """Toggle sensor active state."""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    SENSORS_DB[sensor_id]["active"] = not SENSORS_DB[sensor_id]["active"]
    SENSORS_DB[sensor_id]["status"] = "active" if SENSORS_DB[sensor_id]["active"] else "inactive"
    
    return {"message": "Sensor toggled", "sensor": SENSORS_DB[sensor_id]}