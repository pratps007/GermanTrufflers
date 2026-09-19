from fastapi import APIRouter, Body
from typing import Dict, Any, Optional
from app.services.agri_exposure_engine import agri_exposure_engine
from app.services.farmer_advisory_engine import farmer_advisory_engine
from app.services.crop_damage_engine import crop_damage_engine
from app.services.farmer_damage_reporting import farmer_damage_reporting
from app.services.recovery_engine import recovery_engine

router = APIRouter()

@router.get("/agriculture/status")
async def get_agriculture_status():
    """
    Returns high-level status of the agricultural intelligence engine and monitored crop belts.
    """
    exposure = agri_exposure_engine.get_agricultural_exposure(120.0, 24.0)
    return {
        "status": "online",
        "platform": "PRAVAH-X Agriculture Engine",
        "monitored_area_ha": exposure["summary"]["total_monitored_farmland_ha"],
        "exposed_farms_count": exposure["summary"]["farms_exposed_count"],
        "crops_monitored": [c["crop_name"] for c in exposure["crops"]],
        "districts": exposure["summary"]["affected_districts"]
    }

@router.get("/agriculture/exposure")
async def get_agriculture_exposure(rainfall_mm: float = 120.0, waterlogging_hours: float = 24.0):
    """
    Returns agricultural spatial exposure and crop stage vulnerabilities.
    """
    return agri_exposure_engine.get_agricultural_exposure(rainfall_mm, waterlogging_hours)

@router.get("/agriculture/risk")
async def get_agriculture_risk(rainfall_mm: float = 120.0, waterlogging_hours: float = 24.0):
    """
    Returns crop risk scores and waterlogging submergence ratings.
    """
    exposure = agri_exposure_engine.get_agricultural_exposure(rainfall_mm, waterlogging_hours)
    damage = crop_damage_engine.estimate_damage(rainfall_mm, waterlogging_hours)
    return {
        "exposure_summary": exposure["summary"],
        "crop_risk_profiles": exposure["crops"],
        "estimated_damage": damage["summary"]
    }

@router.get("/agriculture/advisories")
async def get_agriculture_advisories(rainfall_mm: float = 120.0, waterlogging_hours: float = 24.0, lang: str = "en"):
    """
    Returns evidence-backed farmer advisories with ICAR/IMD Agromet provenance.
    """
    return farmer_advisory_engine.generate_advisories(rainfall_mm, waterlogging_hours, lang=lang)

@router.post("/agriculture/scenario")
async def run_agriculture_scenario(payload: Dict[str, Any] = Body(...)):
    """
    Runs a custom agricultural what-if scenario.
    """
    rainfall_mm = float(payload.get("rainfall_mm", 150.0))
    waterlogging_hours = float(payload.get("waterlogging_hours", 36.0))
    lang = str(payload.get("lang", "en"))

    exposure = agri_exposure_engine.get_agricultural_exposure(rainfall_mm, waterlogging_hours)
    advisories = farmer_advisory_engine.generate_advisories(rainfall_mm, waterlogging_hours, lang=lang)
    damage = crop_damage_engine.estimate_damage(rainfall_mm, waterlogging_hours)

    return {
        "scenario": {
            "rainfall_mm": rainfall_mm,
            "waterlogging_hours": waterlogging_hours
        },
        "exposure": exposure,
        "advisories": advisories,
        "damage": damage
    }

@router.get("/agriculture/recovery")
async def get_agriculture_recovery():
    """
    Returns agricultural recovery priority recommendations.
    """
    return recovery_engine.calculate_recovery_priorities(1.2)

@router.post("/agriculture/damage-report")
async def submit_farmer_damage_report(payload: Dict[str, Any] = Body(...)):
    """
    Intake endpoint for farmer damage reporting.
    """
    return farmer_damage_reporting.add_report(payload)
