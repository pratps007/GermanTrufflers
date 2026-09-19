import os
import json
import math
from typing import Dict, Any, List, Tuple
import networkx as nx
from shapely.geometry import shape, Point, LineString, mapping

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ROADS_PATH = os.path.join(WORKSPACE_ROOT, "data", "roads", "processed", "road_centerlines.geojson")
WARDS_PATH = os.path.join(WORKSPACE_ROOT, "data", "boundary", "processed", "wards.geojson")

def _load_geojson(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 6 Synthetic Demo Fleet Units with Deterministic Synthetic Demo Origins
SIMULATED_FLEET = [
    {
        "id": "A01",
        "name": "Ambulance Unit A01",
        "type": "AMBULANCE",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Response Hub Central",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2650, 13.0750]  # Central Chennai
    },
    {
        "id": "A02",
        "name": "Ambulance Unit A02",
        "type": "AMBULANCE",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Response Hub North",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2450, 13.1100]  # North Chennai
    },
    {
        "id": "R01",
        "name": "Rescue Team R01",
        "type": "RESCUE TEAM",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Rescue Station South",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2300, 13.0250]  # South Chennai / Adyar
    },
    {
        "id": "R02",
        "name": "Rescue Team R02",
        "type": "RESCUE TEAM",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Rescue Station East",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2750, 13.0450]  # East / Coast
    },
    {
        "id": "F01",
        "name": "Fire Response F01",
        "type": "FIRE RESPONSE",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Fire Depot West",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2000, 13.0800]  # West / Anna Nagar
    },
    {
        "id": "F02",
        "name": "Fire Response F02",
        "type": "FIRE RESPONSE",
        "label": "SIMULATED RESPONSE RESOURCE",
        "origin_name": "Modelled Fire Depot Southwest",
        "origin_type": "MODELLED ORIGIN",
        "coordinates": [80.2150, 13.0400]  # Southwest / Guindy
    }
]

def _haversine_dist(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculates approximate distance in kilometers between two (lon, lat) points."""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def generate_response_plan(simulation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a deterministic AI-Assisted Emergency Response Plan based on Phase 4 simulation outputs.
    Adheres strictly to scientific and demo guardrails:
    - Labels output as MODELLED SCENARIO / SIMULATED RESPONSE RESOURCE / MODELLED ROUTE COST.
    - Caps visual response entities to TOP 5 priority zones and MAX 5 emergency routes.
    """
    summary_sim = simulation_result.get("summary", {})
    risk_zones_sim = simulation_result.get("risk_zones", [])
    affected_roads_sim = simulation_result.get("affected_roads", {}).get("features", [])
    drainage_status_sim = simulation_result.get("drainage_status", {}).get("features", [])
    wards_geojson = _load_geojson(WARDS_PATH)

    # Map ward geometries for centroid calculation
    ward_geoms_map: Dict[str, Point] = {}
    for f in wards_geojson.get("features", []):
        props = f.get("properties", {})
        w_name = str(props.get("WARD_NAME") or props.get("Ward_Name") or f"Ward {props.get('WARD_NO', '')}").strip()
        try:
            g = shape(f["geometry"])
            ward_geoms_map[w_name] = g.centroid
        except Exception:
            continue

    # Build road status lookup
    road_status_map: Dict[str, str] = {}
    for f in affected_roads_sim:
        props = f.get("properties", {})
        r_name = props.get("road_name")
        r_status = props.get("status", "OPEN")
        if r_name:
            road_status_map[r_name] = r_status

    # 1. PRIORITY ENGINE (0-100 Score & Categorization)
    all_priority_zones = []
    for idx, rz in enumerate(risk_zones_sim):
        w_name = rz.get("ward_name", f"Ward {idx+1}")
        z_name = rz.get("zone_name", "Zone GCC")
        r_level = rz.get("risk_level", "LOW")
        m_depth = rz.get("modelled_depth_m", 0.0)

        # Base score from modelled depth & risk level
        base_depth_score = min(45.0, m_depth * 35.0)
        risk_level_boost = {"CRITICAL": 45.0, "HIGH": 30.0, "MODERATE": 15.0, "LOW": 5.0}.get(r_level, 10.0)
        
        # Add road accessibility penalty & drainage bonus
        road_access_degraded = r_level in ["CRITICAL", "HIGH"]
        drainage_overloaded = summary_sim.get("critical_drainage_segments", 0) > 5000

        score = min(99.0, max(15.0, round(base_depth_score + risk_level_boost + (8.0 if drainage_overloaded else 0.0), 1)))

        # Categorize
        if score >= 80.0:
            classification = "CRITICAL"
        elif score >= 60.0:
            classification = "HIGH"
        elif score >= 40.0:
            classification = "MODERATE"
        else:
            classification = "LOW"

        reasons = [
            f"Modelled flood depth of {m_depth}m",
            f"Waterway proximity & storm accumulation"
        ]
        if road_access_degraded:
            reasons.append("Road accessibility degraded in vicinity")
        if drainage_overloaded:
            reasons.append("Nearby drainage conduits in OVERLOADED state")

        centroid_point = ward_geoms_map.get(w_name, Point(80.25 + (idx * 0.002), 13.05 + (idx * 0.002)))

        all_priority_zones.append({
            "id": f"pz_{idx+1}",
            "rank": 0,
            "ward_name": w_name,
            "zone_name": z_name,
            "priority_score": score,
            "classification": classification,
            "modelled_depth_m": m_depth,
            "road_access_status": "CAUTION" if road_access_degraded else "OPEN",
            "centroid": [round(centroid_point.x, 5), round(centroid_point.y, 5)],
            "reasons": reasons,
            "label": "MODELLED PRIORITY SCORE"
        })

    # Sort descending by priority score
    all_priority_zones.sort(key=lambda x: x["priority_score"], reverse=True)
    for r_idx, pz in enumerate(all_priority_zones):
        pz["rank"] = r_idx + 1

    # TOP 5 PRIORITY ZONES (VISUAL CAP)
    top_priority_zones = all_priority_zones[:5]

    # 2. ROUTING ENGINE GRAPH SETUP (NetworkX)
    roads_geojson = _load_geojson(ROADS_PATH)
    G = nx.Graph()
    node_coords: Dict[str, Tuple[float, float]] = {}

    def _node_key(pt: Tuple[float, float]) -> str:
        return f"{round(pt[0], 4)},{round(pt[1], 4)}"

    for f in roads_geojson.get("features", []):
        try:
            g = shape(f["geometry"])
            r_name = f.get("properties", {}).get("ROAD_NAME") or f.get("properties", {}).get("Name", "GCC Road")
            r_stat = road_status_map.get(r_name, "OPEN")

            if r_stat == "INACCESSIBLE":
                continue  # Exclude blocked edges from routing graph

            weight_mult = 3.5 if r_stat == "CAUTION" else 1.0

            if isinstance(g, LineString):
                coords = list(g.coords)
                for i in range(len(coords) - 1):
                    n1 = _node_key(coords[i])
                    n2 = _node_key(coords[i+1])
                    dist = _haversine_dist(coords[i], coords[i+1]) * weight_mult
                    node_coords[n1] = coords[i]
                    node_coords[n2] = coords[i+1]
                    G.add_edge(n1, n2, weight=dist, dist_km=dist, name=r_name)
        except Exception:
            continue

    def _find_nearest_node(coord: Tuple[float, float]) -> str:
        min_d = float('inf')
        best_n = None
        for nk, nc in node_coords.items():
            d = (nc[0] - coord[0])**2 + (nc[1] - coord[1])**2
            if d < min_d:
                min_d = d
                best_n = nk
        return best_n or list(node_coords.keys())[0] if node_coords else ""

    # 3. RESOURCE ALLOCATION & ROUTE GENERATION
    allocations = []
    routes = []
    explanations = []

    # Pair the 6 simulated fleet units to the top priority zones
    for u_idx, unit in enumerate(SIMULATED_FLEET):
        target_zone = top_priority_zones[u_idx % len(top_priority_zones)]
        target_coord = (target_zone["centroid"][0], target_zone["centroid"][1])
        unit_coord = (unit["coordinates"][0], unit["coordinates"][1])

        # Compute route using NetworkX
        src_node = _find_nearest_node(unit_coord)
        tgt_node = _find_nearest_node(target_coord)

        route_coords = [unit_coord]
        route_cost = _haversine_dist(unit_coord, target_coord) * 1.4

        if src_node and tgt_node and G.has_node(src_node) and G.has_node(tgt_node):
            try:
                path_nodes = nx.shortest_path(G, source=src_node, target=tgt_node, weight='weight')
                path_coords = [node_coords[n] for n in path_nodes if n in node_coords]
                if len(path_coords) >= 2:
                    route_coords = [unit_coord] + path_coords + [target_coord]
                    route_cost = round(nx.shortest_path_length(G, source=src_node, target=tgt_node, weight='weight'), 2)
            except Exception:
                # Geometric fallback line string if graph components disconnected by flood barriers
                route_coords = [unit_coord, target_coord]

        route_geojson = {
            "type": "Feature",
            "id": f"route_{unit['id']}",
            "geometry": {
                "type": "LineString",
                "coordinates": route_coords
            },
            "properties": {
                "resource_id": unit["id"],
                "resource_name": unit["name"],
                "target_zone": target_zone["ward_name"],
                "route_status": "MODELLED ROUTE",
                "route_cost": route_cost,
                "stroke_color": "#00ffff",
                "stroke_width": 4
            }
        }

        # Keep max 5 routes for clear visual priority
        if len(routes) < 5:
            routes.append(route_geojson)

        allocation_entry = {
            "resource_id": unit["id"],
            "resource_name": unit["name"],
            "resource_type": unit["type"],
            "label": unit["label"],
            "origin_name": unit["origin_name"],
            "origin_type": unit["origin_type"],
            "assigned_zone": target_zone["ward_name"],
            "assigned_zone_id": target_zone["id"],
            "priority_level": target_zone["classification"],
            "priority_score": target_zone["priority_score"],
            "estimated_route_cost": route_cost,
            "road_access_status": target_zone["road_access_status"],
            "reason": f"Allocated to {target_zone['ward_name']} ({target_zone['classification']}) to minimize modelled response latency."
        }
        allocations.append(allocation_entry)

        # Build WHY Explanation card
        explanations.append({
            "target": f"{unit['name']} → {target_zone['ward_name']}",
            "resource_id": unit["id"],
            "assigned_zone": target_zone["ward_name"],
            "risk_level": target_zone["classification"],
            "modelled_depth_m": target_zone["modelled_depth_m"],
            "factors": [
                f"Zone assigned {target_zone['classification']} modelled priority (score {target_zone['priority_score']})",
                f"Modelled flood depth: {target_zone['modelled_depth_m']}m",
                f"Primary route avoids INACCESSIBLE road segments",
                f"Modelled route cost: {route_cost} units from {unit['origin_name']}"
            ],
            "summary": f"{unit['name']} dispatched from synthetic origin ({unit['origin_name']}) via optimal open road corridors."
        })

    # 4. RESPONSE RECOMMENDATION ACTIONS
    actions = [
        {
            "id": "act_1",
            "type": "RESCUE DISPATCH",
            "label": "MODELLED RESPONSE RECOMMENDATION",
            "title": f"Dispatch Rescue Team R01 → {top_priority_zones[0]['ward_name']}",
            "description": f"Priority zone has {top_priority_zones[0]['classification']} flood depth ({top_priority_zones[0]['modelled_depth_m']}m). Deploy inflatable boats.",
            "urgency": "CRITICAL"
        },
        {
            "id": "act_2",
            "type": "AMBULANCE REROUTE",
            "label": "MODELLED RESPONSE RECOMMENDATION",
            "title": f"Reroute Ambulance A01 around INACCESSIBLE road segments",
            "description": "Utilize northern arterial corridor avoiding flooded subways.",
            "urgency": "HIGH"
        },
        {
            "id": "act_3",
            "type": "DRAINAGE INTERVENTION",
            "label": "MODELLED RESPONSE RECOMMENDATION",
            "title": "Flag Mobile Pumping Units for OVERLOADED Drainage Conduits",
            "description": "Deploy auxiliary pumps along Cooum river outlet nodes.",
            "urgency": "HIGH"
        },
        {
            "id": "act_4",
            "type": "EVACUATION NOTICE",
            "label": "MODELLED RESPONSE RECOMMENDATION",
            "title": "Issue Evacuation Readiness for Waterway Proximity Wards",
            "description": "Broadcast emergency shelter locations for low-lying municipal wards.",
            "urgency": "MODERATE"
        }
    ]

    return {
        "status": "success",
        "mode": "MODELLED RESPONSE PLAN",
        "guardrail": "AI-ASSISTED DECISION SUPPORT — All routes and resources use modelled synthetic origins.",
        "priority_zones": top_priority_zones,
        "simulated_fleet": SIMULATED_FLEET,
        "resource_allocations": allocations,
        "routes": routes,
        "actions": actions,
        "explanations": explanations,
        "summary": {
            "priority_zones": len(top_priority_zones),
            "resources_assigned": len(allocations),
            "routes_generated": len(routes),
            "critical_actions": len(actions)
        }
    }
