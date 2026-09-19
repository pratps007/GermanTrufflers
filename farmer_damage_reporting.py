import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DamageReportItem(BaseModel):
    report_id: str
    farmer_id: str
    farm_id: str
    location_name: str
    latitude: float
    longitude: float
    crop: str
    crop_stage: str
    event_type: str
    damage_type: str
    waterlogging_duration_hours: float
    estimated_damage_pct: float
    insurance_status: str  # ENROLLED_PMFBY, NOT_ENROLLED, UNKNOWN
    photo_url: Optional[str] = None
    timestamp: str
    status: str  # REPORTED, UNDER_REVIEW, FIELD_VERIFIED, ASSESSED, RESOLUTION_INITIATED

class FarmerDamageReportingService:
    def __init__(self):
        self._reports: List[DamageReportItem] = self._init_sample_reports()

    def _init_sample_reports(self) -> List[DamageReportItem]:
        return [
            DamageReportItem(
                report_id="RPT_2026_001",
                farmer_id="FRM_TN_10842",
                farm_id="FRM_PLOT_92",
                location_name="Tiruvallur West Sector",
                latitude=13.142,
                longitude=79.910,
                crop="Paddy (Samba)",
                crop_stage="FLOWERING",
                event_type="Extreme Rainfall",
                damage_type="Waterlogging & Submergence",
                waterlogging_duration_hours=36.0,
                estimated_damage_pct=75.0,
                insurance_status="ENROLLED_PMFBY",
                photo_url="/static/sample_crop_flood.jpg",
                timestamp="2026-09-19T06:15:00Z",
                status="REPORTED"
            ),
            DamageReportItem(
                report_id="RPT_2026_002",
                farmer_id="FRM_TN_11905",
                farm_id="FRM_PLOT_104",
                location_name="Kanchipuram North Belt",
                latitude=12.834,
                longitude=79.702,
                crop="Groundnut",
                crop_stage="VEGETATIVE",
                event_type="Urban Overflow",
                damage_type="Root Rot & Siltation",
                waterlogging_duration_hours=24.0,
                estimated_damage_pct=50.0,
                insurance_status="ENROLLED_PMFBY",
                photo_url=None,
                timestamp="2026-09-19T06:45:00Z",
                status="UNDER_REVIEW"
            )
        ]

    def add_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        report_id = f"RPT_{int(time.time())}"
        new_report = DamageReportItem(
            report_id=report_id,
            farmer_id=report_data.get("farmer_id", "FRM_DEMO_GUEST"),
            farm_id=report_data.get("farm_id", "PLOT_DEMO_01"),
            location_name=report_data.get("location_name", "Chennai Peri-urban Farm"),
            latitude=float(report_data.get("latitude", 13.0827)),
            longitude=float(report_data.get("longitude", 80.2707)),
            crop=report_data.get("crop", "Paddy"),
            crop_stage=report_data.get("crop_stage", "FLOWERING"),
            event_type=report_data.get("event_type", "Extreme Monsoon"),
            damage_type=report_data.get("damage_type", "Submergence"),
            waterlogging_duration_hours=float(report_data.get("waterlogging_duration_hours", 24.0)),
            estimated_damage_pct=float(report_data.get("estimated_damage_pct", 60.0)),
            insurance_status=report_data.get("insurance_status", "ENROLLED_PMFBY"),
            photo_url=report_data.get("photo_url"),
            timestamp="2026-09-19T07:20:00Z",
            status="REPORTED"
        )
        self._reports.append(new_report)
        return {
            "status": "success",
            "message": "Farmer damage report received and logged into PRAVAH-X intake workflow.",
            "report": new_report.model_dump()
        }

    def get_all_reports(self) -> List[Dict[str, Any]]:
        return [r.model_dump() for r in self._reports]

farmer_damage_reporting = FarmerDamageReportingService()
