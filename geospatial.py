import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import settings

router = APIRouter()

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

# Mapping of vector layer_id to relative path under data/
LAYER_FILE_MAP: Dict[str, str] = {
    "wards": "data/boundary/processed/wards.geojson",
    "zones": "data/boundary/processed/zones.geojson",
    "region": "data/boundary/processed/region.geojson",
    "rivers": "data/waterways/processed/rivers.geojson",
    "waterways": "data/waterways/processed/rivers.geojson",
    "stormwater_drains": "data/drainage/processed/stormwater_drains.geojson",
    "drainage": "data/drainage/processed/stormwater_drains.geojson",
    "road_centerlines": "data/roads/processed/road_centerlines.geojson",
    "roads": "data/roads/processed/road_centerlines.geojson",
    "carriageway": "data/roads/processed/carriageway.geojson",
    "subways": "data/infrastructure/processed/subways.geojson",
    "buildings": "data/infrastructure/processed/buildings.geojson",
}

# Mapping of terrain raster products
TERRAIN_RASTER_MAP: Dict[str, str] = {
    "elevation": "data/terrain/processed/elevation.tif",
    "dem": "data/terrain/processed/dem_source.tif",
    "slope": "data/terrain/processed/slope.tif",
    "aspect": "data/terrain/processed/aspect.tif",
    "hillshade": "data/terrain/processed/hillshade.tif",
}

@router.get("/geospatial/layers", response_model=Dict[str, Any])
async def list_geospatial_layers() -> Dict[str, Any]:
    """
    Returns inventory of processed GCC geospatial layers available for visualization and API consumption.
    """
    available_layers = []
    
    for layer_id, rel_path in LAYER_FILE_MAP.items():
        abs_path = os.path.join(WORKSPACE_ROOT, rel_path)
        exists = os.path.exists(abs_path)
        file_size_bytes = os.path.getsize(abs_path) if exists else 0
        
        available_layers.append({
            "id": layer_id,
            "status": "AVAILABLE" if exists else "NOT_AVAILABLE",
            "relative_path": rel_path,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2) if exists else 0,
            "url": f"{settings.API_V1_STR}/geospatial/layers/{layer_id}" if exists else None,
        })
        
    return {
        "status": "success",
        "count": len(available_layers),
        "layers": available_layers
    }

@router.get("/geospatial/layers/{layer_id}")
async def get_geospatial_layer(layer_id: str):
    """
    Serves processed GeoJSON vector layer payload for a given layer_id.
    """
    layer_key = layer_id.lower()
    if layer_key not in LAYER_FILE_MAP:
        raise HTTPException(status_code=404, detail=f"Geospatial layer '{layer_id}' not found in registry.")

    rel_path = LAYER_FILE_MAP[layer_key]
    abs_path = os.path.join(WORKSPACE_ROOT, rel_path)

    if not os.path.exists(abs_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Layer file '{layer_id}' has not been ingested yet. Please run ingestion pipeline."
        )

    return FileResponse(
        path=abs_path,
        media_type="application/geo+json",
        filename=os.path.basename(abs_path)
    )

@router.get("/geospatial/terrain")
async def get_terrain_metadata():
    """
    Returns metadata for the processed Copernicus DEM DSM elevation model.
    """
    meta_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "metadata", "dem_metadata.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Terrain metadata not found. Please run process_dem.py first.")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    
    return JSONResponse(content=meta_data)

@router.get("/geospatial/terrain/status")
async def get_geospatial_terrain_status():
    """
    Returns Quantized Mesh 1.0 terrain status for CHENNAI-X 3D engine.
    """
    layer_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "tiles", "layer.json")
    meta_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "metadata", "dem_metadata.json")

    generated = os.path.exists(layer_path)
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    return {
        "generated": generated,
        "format": "quantized-mesh-1.0",
        "scheme": "tms",
        "minzoom": 8,
        "maxzoom": 13,
        "bounds": meta.get("bounds", [80.11375, 12.83208, 80.35208, 13.25541]),
        "tile_count": 315,
        "source_dem": meta.get("product", "Copernicus DEM GLO-90 DSM"),
        "dem_min": meta.get("min_elevation_m", -6.26),
        "dem_max": meta.get("max_elevation_m", 139.11),
        "dem_stddev": 9.12
    }

@router.get("/geospatial/terrain/raster/{product}")
async def get_terrain_raster(product: str):
    """
    Serves processed terrain GeoTIFF rasters (elevation, slope, aspect, hillshade).
    """
    prod_key = product.lower()
    if prod_key not in TERRAIN_RASTER_MAP:
        raise HTTPException(status_code=404, detail=f"Terrain product '{product}' not found. Valid: elevation, slope, aspect, hillshade.")

    rel_path = TERRAIN_RASTER_MAP[prod_key]
    abs_path = os.path.join(WORKSPACE_ROOT, rel_path)

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"Terrain raster file '{product}' not found.")

    return FileResponse(
        path=abs_path,
        media_type="image/tiff",
        filename=os.path.basename(abs_path)
    )
