from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from fastapi import APIRouter
from app.services.response_orchestrator import generate_response_plan

router = APIRouter()

class ResponsePlanRequest(BaseModel):
    simulation: Dict[str, Any] = Field(description="Phase 4 flood simulation output dictionary")

@router.post("/response/plan")
async def create_response_plan(request: ResponsePlanRequest) -> Dict[str, Any]:
    """
    Executes AI-Assisted Emergency Response Orchestrator.
    Ranks priority zones (0-100), allocates simulated emergency fleet, generates modelled routes avoiding INACCESSIBLE roads.
    """
    plan = generate_response_plan(request.simulation)
    return plan
