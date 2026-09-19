from fastapi import APIRouter, Body
from typing import Dict, Any
from app.services.data_fusion_engine import data_fusion_engine
from app.services.model_validation import model_validation

router = APIRouter()

@router.post("/event/analyze")
async def analyze_event(payload: Dict[str, Any] = Body(...)):
    """
    Fuses all spatial, weather, road, facility, and agricultural intelligence into a unified PRAVAH-X Event Graph.
    """
    rainfall_mm = float(payload.get("rainfall_mm", 120.0))
    duration_hours = float(payload.get("duration_hours", 12.0))
    drainage_capacity_pct = float(payload.get("drainage_capacity_pct", 60.0))
    tidal_condition = str(payload.get("tidal_condition", "Elevated"))

    event_graph = data_fusion_engine.fuse_event_graph(
        rainfall_mm, duration_hours, drainage_capacity_pct, tidal_condition
    )
    validation = model_validation.validate_against_historical_2015()

    return {
        "status": "success",
        "platform": "PRAVAH-X Multi-Hazard Platform",
        "event_graph": event_graph,
        "historical_validation": validation
    }

@router.post("/event/what-if")
async def run_what_if_scenario(payload: Dict[str, Any] = Body(...)):
    """
    Compares Baseline event vs What-If Scenario (higher rainfall, lower drainage, road failures).
    """
    baseline_rain = float(payload.get("baseline_rainfall_mm", 120.0))
    scenario_rain = float(payload.get("scenario_rainfall_mm", 180.0))
    drainage_pct = float(payload.get("drainage_capacity_pct", 40.0))

    baseline_graph = data_fusion_engine.fuse_event_graph(baseline_rain, 12.0, 70.0, "Normal")
    scenario_graph = data_fusion_engine.fuse_event_graph(scenario_rain, 12.0, drainage_pct, "High")

    b_depth = baseline_graph["hazard"]["max_modelled_depth_m"]
    s_depth = scenario_graph["hazard"]["max_modelled_depth_m"]

    b_inaccess = baseline_graph["road_impact"]["inaccessible_roads"]
    s_inaccess = scenario_graph["road_impact"]["inaccessible_roads"]

    return {
        "status": "success",
        "comparison": {
            "baseline": {
                "rainfall_mm": baseline_rain,
                "max_depth_m": b_depth,
                "inaccessible_roads": b_inaccess,
                "exposed_population": baseline_graph["human_exposure"]["estimated_exposed_population"]
            },
            "scenario": {
                "rainfall_mm": scenario_rain,
                "max_depth_m": s_depth,
                "inaccessible_roads": s_inaccess,
                "exposed_population": scenario_graph["human_exposure"]["estimated_exposed_population"]
            },
            "deltas": {
                "additional_depth_m": round(s_depth - b_depth, 2),
                "additional_inaccessible_roads": s_inaccess - b_inaccess,
                "additional_exposed_population": scenario_graph["human_exposure"]["estimated_exposed_population"] - baseline_graph["human_exposure"]["estimated_exposed_population"]
            }
        },
        "scenario_event_graph": scenario_graph
    }
