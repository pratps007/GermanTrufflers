from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from fastapi import APIRouter
from app.services.simulation_engine import run_flood_simulation

router = APIRouter()

class SimulationRequest(BaseModel):
    event_type: str = Field(default="Urban Flood")
    rainfall_mm: float = Field(default=120.0, ge=0, le=500)
    duration_hours: float = Field(default=12.0, ge=1, le=72)
    drainage_capacity: float = Field(default=60.0, ge=0, le=100)
    tide: str = Field(default="Normal")
    road_disruption: bool = Field(default=False)
    resource_availability: str = Field(default="Normal")

@router.post("/simulation/run")
async def execute_simulation(request: SimulationRequest) -> Dict[str, Any]:
    """
    Executes a deterministic urban flood consequence scenario simulation.
    Returns modelled flood polygons, affected road segments, drainage load, and risk explanations.
    """
    result = run_flood_simulation(
        event_type=request.event_type,
        rainfall_mm=request.rainfall_mm,
        duration_hours=request.duration_hours,
        drainage_capacity=request.drainage_capacity,
        tide=request.tide,
        road_disruption=request.road_disruption,
        resource_availability=request.resource_availability
    )
    return result
