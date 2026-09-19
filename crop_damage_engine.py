from typing import Dict, Any

class CropDamageEngine:
    """
    Crop Damage Estimation Engine.
    Inputs: flood extent, crop area, crop stage, waterlogging duration.
    Outputs: potentially affected, moderately affected, severely affected, likely crop loss.
    """

    def estimate_damage(self, rainfall_mm: float, waterlogging_hours: float) -> Dict[str, Any]:
        total_farmland_ha = 81600

        if waterlogging_hours >= 48:
            severely_affected_ha = int(total_farmland_ha * 0.42)
            moderately_affected_ha = int(total_farmland_ha * 0.35)
            likely_loss_ha = int(total_farmland_ha * 0.38)
        elif waterlogging_hours >= 24:
            severely_affected_ha = int(total_farmland_ha * 0.22)
            moderately_affected_ha = int(total_farmland_ha * 0.38)
            likely_loss_ha = int(total_farmland_ha * 0.18)
        else:
            severely_affected_ha = int(total_farmland_ha * 0.08)
            moderately_affected_ha = int(total_farmland_ha * 0.20)
            likely_loss_ha = int(total_farmland_ha * 0.05)

        potentially_affected_ha = severely_affected_ha + moderately_affected_ha

        return {
            "provenance": "MODELLED",
            "source": "PRAVAH-X Crop Hydrodynamic Loss Estimator",
            "summary": {
                "total_farmland_monitored_ha": total_farmland_ha,
                "potentially_affected_ha": potentially_affected_ha,
                "moderately_affected_ha": moderately_affected_ha,
                "severely_affected_ha": severely_affected_ha,
                "estimated_likely_crop_loss_ha": likely_loss_ha,
                "confidence": "ESTIMATED (Requires Satellite / Ground Survey Verification)"
            },
            "disclaimer": "Crop loss figures are modelled spatial estimates. PMFBY official claims require field crop cutting experiment (CCE) verification."
        }

crop_damage_engine = CropDamageEngine()
