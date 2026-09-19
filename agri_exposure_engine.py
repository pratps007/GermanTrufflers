from typing import Dict, Any, List

class AgriExposureEngine:
    """
    Agricultural Spatial Exposure Engine.
    Identifies agricultural areas, crop areas, crop stages (SEEDING, GERMINATION, VEGETATIVE, FLOWERING, FRUITING, MATURITY, HARVEST, POST-HARVEST),
    and crop risk scores.
    Provenance: MODELLED / ICAR-CRIDA PROXY.
    """

    def get_agricultural_exposure(self, rainfall_mm: float, waterlogging_hours: float) -> Dict[str, Any]:
        # Major peri-urban agricultural belts in Kanchipuram, Tiruvallur & Chengalpattu adjacent to GCC
        crops_data = [
            {
                "crop_name": "Paddy (Samba / Thaladi)",
                "district": "Tiruvallur & Kanchipuram Belt",
                "crop_area_ha": 42500,
                "crop_stage": "FLOWERING",
                "waterlogging_tolerance_hours": 48,
                "current_waterlogging_hours": waterlogging_hours,
                "risk_level": "CRITICAL" if waterlogging_hours >= 48 else ("HIGH" if waterlogging_hours >= 24 else "MODERATE"),
                "risk_score": 92 if waterlogging_hours >= 48 else (75 if waterlogging_hours >= 24 else 45),
                "reasons": [
                    "Submerged at flowering stage leading to spikelet sterility",
                    f"Waterlogging duration ({waterlogging_hours}h) exceeds tolerance limit",
                    "Poor field drainage outflow"
                ]
            },
            {
                "crop_name": "Groundnut",
                "district": "Chengalpattu Belt",
                "crop_area_ha": 18200,
                "crop_stage": "VEGETATIVE",
                "waterlogging_tolerance_hours": 24,
                "current_waterlogging_hours": waterlogging_hours,
                "risk_level": "HIGH" if waterlogging_hours >= 24 else "MODERATE",
                "risk_score": 84 if waterlogging_hours >= 24 else 50,
                "reasons": [
                    "High susceptibility to root rot in waterlogged soils",
                    "Excess rainfall in vegetative phase"
                ]
            },
            {
                "crop_name": "Pulses (Blackgram / Greengram)",
                "district": "Kanchipuram District",
                "crop_area_ha": 12400,
                "crop_stage": "SEEDING",
                "waterlogging_tolerance_hours": 12,
                "current_waterlogging_hours": waterlogging_hours,
                "risk_level": "CRITICAL" if waterlogging_hours >= 12 else "HIGH",
                "risk_score": 96 if waterlogging_hours >= 12 else 78,
                "reasons": [
                    "Seedling mortality due to anaerobic soil condition",
                    "Heavy surface crusting post-drainage"
                ]
            },
            {
                "crop_name": "Horticulture (Vegetables / Chillies)",
                "district": "Peri-urban Chennai Belt",
                "crop_area_ha": 8500,
                "crop_stage": "FRUITING",
                "waterlogging_tolerance_hours": 18,
                "current_waterlogging_hours": waterlogging_hours,
                "risk_level": "HIGH" if waterlogging_hours >= 18 else "MODERATE",
                "risk_score": 88 if waterlogging_hours >= 18 else 60,
                "reasons": [
                    "Fruit rot and damping off",
                    "Market transport access cutoff due to road waterlogging"
                ]
            }
        ]

        total_area_ha = sum(c["crop_area_ha"] for c in crops_data)
        high_risk_area_ha = sum(c["crop_area_ha"] for c in crops_data if c["risk_level"] in ["CRITICAL", "HIGH"])

        return {
            "provenance": "MODELLED",
            "source_authority": "ICAR-CRIDA District Contingency Plan & State Dept of Agriculture Proxy",
            "summary": {
                "total_monitored_farmland_ha": total_area_ha,
                "high_risk_crop_area_ha": high_risk_area_ha,
                "farms_exposed_count": int(total_area_ha / 1.8),
                "affected_districts": ["Tiruvallur", "Kanchipuram", "Chengalpattu"]
            },
            "crops": crops_data
        }

agri_exposure_engine = AgriExposureEngine()
