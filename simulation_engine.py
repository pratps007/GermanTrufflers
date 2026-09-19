import os
import json
from typing import Dict, Any, List
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Paths to authoritative GCC GeoJSON datasets
RIVERS_PATH = os.path.join(WORKSPACE_ROOT, "data", "waterways", "processed", "rivers.geojson")
WARDS_PATH = os.path.join(WORKSPACE_ROOT, "data", "boundary", "processed", "wards.geojson")
ROADS_PATH = os.path.join(WORKSPACE_ROOT, "data", "roads", "processed", "road_centerlines.geojson")
DRAINS_PATH = os.path.join(WORKSPACE_ROOT, "data", "drainage", "processed", "stormwater_drains.geojson")

def _load_geojson(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_flood_simulation(
    event_type: str,
    rainfall_mm: float,
    duration_hours: float,
    drainage_capacity: float,
    tide: str,
    road_disruption: bool = False,
    resource_availability: str = "Normal"
) -> Dict[str, Any]:
    """
    Executes a transparent, deterministic flood consequence scenario simulation
    anchored to real Greater Chennai Corporation (GCC) GIS geometry.
    """
    # 1. Deterministic Multipliers
    rainfall_factor = max(0.5, float(rainfall_mm) / 100.0)
    drainage_factor = max(0.4, 1.5 - (float(drainage_capacity) / 100.0))
    duration_factor = 1.0 + (float(duration_hours) / 48.0)
    
    tide_multipliers = {"Normal": 1.0, "Elevated": 1.35, "High": 1.75}
    tide_factor = tide_multipliers.get(tide, 1.0)

    base_severity = rainfall_factor * drainage_factor * duration_factor * tide_factor
    max_modelled_depth = min(1.95, round(0.35 * base_severity, 2))

    # 2. Load River Geometries for Spatial Anchoring
    rivers_geojson = _load_geojson(RIVERS_PATH)
    river_geoms = []
    for f in rivers_geojson.get("features", []):
        try:
            g = shape(f["geometry"])
            if g.is_valid:
                river_geoms.append(g)
        except Exception:
            continue

    if river_geoms:
        combined_rivers = unary_union(river_geoms)
    else:
        from shapely.geometry import Point
        combined_rivers = Point(80.25, 13.05)

    # 3. Generate Scenario Flood Influence Polygons
    buffer_high = 0.003 + (0.0035 * base_severity)
    buffer_mod = buffer_high * 1.5
    buffer_low = buffer_high * 2.2

    geom_high = combined_rivers.buffer(buffer_high)
    geom_mod = combined_rivers.buffer(buffer_mod).difference(geom_high)
    geom_low = combined_rivers.buffer(buffer_low).difference(combined_rivers.buffer(buffer_mod))

    flood_features = []
    zones_def = [
        ("CRITICAL", geom_high, max_modelled_depth, "#ef4444", 0.65),
        ("HIGH", geom_mod, round(max_modelled_depth * 0.65, 2), "#f97316", 0.50),
        ("MODERATE", geom_low, round(max_modelled_depth * 0.35, 2), "#eab308", 0.35),
    ]

    for idx, (risk_lbl, geom, depth_m, col, opacity) in enumerate(zones_def):
        if not geom.is_empty:
            flood_features.append({
                "type": "Feature",
                "id": f"flood_poly_{idx}",
                "geometry": mapping(geom),
                "properties": {
                    "simulation_type": "MODELLED SCENARIO",
                    "risk_level": risk_lbl,
                    "modelled_depth_m": depth_m,
                    "fill_color": col,
                    "fill_opacity": opacity,
                    "stroke_color": col,
                    "stroke_width": 2,
                    "rainfall_mm": rainfall_mm,
                    "drainage_capacity_percent": drainage_capacity,
                    "tide_condition": tide,
                    "duration_hours": duration_hours
                }
            })

    # 4. Process GCC Ward Risk Intersections & Explanations
    wards_geojson = _load_geojson(WARDS_PATH)
    risk_zones = []
    explanations = []
    critical_zones_count = 0

    for idx, f in enumerate(wards_geojson.get("features", [])):
        props = f.get("properties", {})
        ward_name = props.get("WARD_NAME") or props.get("Ward_Name") or f"Ward {props.get('WARD_NO', idx+1)}"
        zone_name = props.get("ZONE_NAME") or f"Zone {props.get('ZONE_NO', 'GCC')}"

        try:
            w_geom = shape(f["geometry"])
            inter_high = w_geom.intersection(geom_high).area / max(w_geom.area, 1e-9)
            inter_mod = w_geom.intersection(geom_mod).area / max(w_geom.area, 1e-9)
        except Exception:
            inter_high, inter_mod = 0.0, 0.0

        if inter_high > 0.10:
            w_risk = "CRITICAL"
            w_depth = max_modelled_depth
            critical_zones_count += 1
        elif inter_high > 0.02 or inter_mod > 0.15:
            w_risk = "HIGH"
            w_depth = round(max_modelled_depth * 0.7, 2)
            critical_zones_count += 1
        elif inter_mod > 0.02:
            w_risk = "MODERATE"
            w_depth = round(max_modelled_depth * 0.4, 2)
        else:
            w_risk = "LOW"
            w_depth = round(max_modelled_depth * 0.15, 2)

        reason_str = f"Rainfall: {rainfall_mm}mm | Drainage: {drainage_capacity}% | Tide: {tide}"
        if w_risk in ["CRITICAL", "HIGH"]:
            reason_str += f" | High waterway proximity & {duration_hours}h storm accumulation"

        risk_zones.append({
            "ward_name": str(ward_name),
            "zone_name": str(zone_name),
            "risk_level": w_risk,
            "modelled_depth_m": w_depth,
            "reason": reason_str
        })

        if len(explanations) < 5 and w_risk in ["CRITICAL", "HIGH"]:
            explanations.append({
                "target": f"{ward_name} ({zone_name})",
                "risk_level": w_risk,
                "modelled_depth_m": w_depth,
                "factors": [
                    f"Rainfall scenario: {rainfall_mm} mm",
                    f"Drainage capacity: {drainage_capacity}%",
                    f"Waterway proximity: HIGH ({tide} tide condition)",
                    f"Accumulation duration: {duration_hours} hours"
                ],
                "summary": "Risk generated from configured scenario parameters and GCC spatial geometry."
            })

    # 5. Process GCC Roads Intersections & Inaccessibility
    roads_geojson = _load_geojson(ROADS_PATH)
    affected_road_features = []
    affected_roads_count = 0

    for idx, f in enumerate(roads_geojson.get("features", [])):
        props = f.get("properties", {})
        road_name = props.get("ROAD_NAME") or props.get("Name") or f"GCC Road Segment {idx+1}"
        
        try:
            r_geom = shape(f["geometry"])
            if r_geom.intersects(geom_high):
                r_status = "INACCESSIBLE"
                r_depth = max_modelled_depth
                r_color = "#ef4444"
                affected_roads_count += 1
            elif r_geom.intersects(geom_mod):
                r_status = "CAUTION"
                r_depth = round(max_modelled_depth * 0.5, 2)
                r_color = "#f59e0b"
                affected_roads_count += 1
            else:
                r_status = "OPEN"
                r_depth = 0.0
                r_color = "#10b981"
        except Exception:
            continue

        if r_status != "OPEN":
            affected_road_features.append({
                "type": "Feature",
                "id": f"road_affected_{idx}",
                "geometry": f["geometry"],
                "properties": {
                    "road_name": str(road_name),
                    "status": r_status,
                    "modelled_depth_m": r_depth,
                    "stroke_color": r_color,
                    "stroke_width": 4 if r_status == "INACCESSIBLE" else 3
                }
            })

    affected_road_features = affected_road_features[:600]

    # 6. Process GCC Stormwater Drain Modelled Load
    drains_geojson = _load_geojson(DRAINS_PATH)
    drainage_features = []
    critical_drains_count = 0
    d_load_pct = min(100, round((rainfall_factor * 55.0) / (drainage_capacity / 100.0 + 0.1), 1))

    for idx, f in enumerate(drains_geojson.get("features", [])):
        props = f.get("properties", {})
        if d_load_pct > 80:
            d_status = "OVERLOADED"
            d_color = "#d946ef"
            critical_drains_count += 1
        elif d_load_pct > 50:
            d_status = "STRESSED"
            d_color = "#f97316"
            critical_drains_count += 1
        else:
            d_status = "NORMAL"
            d_color = "#06b6d4"

        if idx < 400:
            drainage_features.append({
                "type": "Feature",
                "id": f"drain_status_{idx}",
                "geometry": f["geometry"],
                "properties": {
                    "conduit_id": props.get("SWD_ID") or f"SWD-{idx+1}",
                    "modelled_load": "MODELLED DRAINAGE LOAD",
                    "status": d_status,
                    "load_percent": d_load_pct,
                    "stroke_color": d_color,
                    "stroke_width": 3
                }
            })

    return {
        "status": "success",
        "simulation_type": "MODELLED SCENARIO",
        "summary": {
            "critical_zones": critical_zones_count,
            "affected_roads": affected_roads_count,
            "critical_drainage_segments": critical_drains_count,
            "high_risk_areas": len(flood_features),
            "max_modelled_depth_m": max_modelled_depth
        },
        "flood_polygons": {
            "type": "FeatureCollection",
            "features": flood_features
        },
        "affected_roads": {
            "type": "FeatureCollection",
            "features": affected_road_features
        },
        "drainage_status": {
            "type": "FeatureCollection",
            "features": drainage_features
        },
        "risk_zones": risk_zones,
        "explanations": explanations
    }
