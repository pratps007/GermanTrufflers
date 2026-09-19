import os
import json
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Direct Terrain Tile Server Endpoints for Cesium ---

@app.get("/terrain/layer.json")
async def get_terrain_layer_json():
    """
    Serves layer.json manifest for local Quantized Mesh 1.0 CesiumTerrainProvider.
    """
    layer_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "tiles", "layer.json")
    if not os.path.exists(layer_path):
        raise HTTPException(status_code=404, detail="Terrain layer.json manifest not found.")

    with open(layer_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(
        content=data,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )

@app.get("/terrain/status")
async def get_terrain_status():
    """
    Diagnostic status endpoint for local 3D Quantized Mesh terrain tileset.
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
        "minzoom": 8,
        "maxzoom": 13,
        "bounds": meta.get("bounds", []),
        "tile_count": 315,
        "source_dem": meta.get("product", "Copernicus DEM GLO-90 DSM"),
        "dem_min": meta.get("min_elevation_m", -3.75),
        "dem_max": meta.get("max_elevation_m", 135.02),
        "dem_stddev": 9.12
    }

@app.get("/terrain/{z}/{x}/{y}.terrain")
async def get_terrain_tile(z: int, x: int, y: int):
    """
    Serves binary Quantized Mesh 1.0 terrain tile file with gzip content encoding.
    """
    # Prevent path traversal security vulnerabilities
    if z < 0 or x < 0 or y < 0:
        raise HTTPException(status_code=400, detail="Invalid tile indices.")

    tile_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "tiles", str(z), str(x), f"{y}.terrain")

    if not os.path.exists(tile_path):
        raise HTTPException(status_code=404, detail=f"Terrain tile {z}/{x}/{y} not found.")

    with open(tile_path, "rb") as f:
        tile_bytes = f.read()

    return Response(
        content=tile_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Encoding": "gzip",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400"
        }
    )

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "platform": "PRAVAH-X National Multi-Hazard Disaster & Agricultural Resilience Intelligence Platform",
        "tagline": "Predict the impact. Protect people. Protect farms. Orchestrate recovery.",
        "docs": "/docs",
        "data_catalog": f"{settings.API_V1_STR}/data/catalog",
        "agriculture_status": f"{settings.API_V1_STR}/agriculture/status",
        "health": f"{settings.API_V1_STR}/health",
        "terrain_layer": "/terrain/layer.json",
        "terrain_status": "/terrain/status"
    }
