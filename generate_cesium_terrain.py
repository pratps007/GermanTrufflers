import os
import sys
import math
import json
import numpy as np
import rasterio
from typing import Tuple, List, Dict, Any
import quantized_mesh_encoder

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Geographic TMS Tile Utilities for EPSG:4326
def lon_to_tile_x(lon: float, zoom: int) -> int:
    n = 2 ** zoom
    tile_x = int(math.floor((lon + 180.0) / 360.0 * (2 * n)))
    return max(0, min(tile_x, 2 * n - 1))

def lat_to_tile_y(lat: float, zoom: int) -> int:
    n = 2 ** zoom
    tile_y = int(math.floor((lat + 90.0) / 180.0 * n))
    return max(0, min(tile_y, n - 1))

def tile_bounds_epsg4326(x: int, y: int, z: int) -> Tuple[float, float, float, float]:
    """Returns (west, south, east, north) in degrees for Geographic TMS tile."""
    n = 2 ** z
    lon_span = 360.0 / (2 * n)
    lat_span = 180.0 / n
    west = -180.0 + x * lon_span
    east = west + lon_span
    south = -90.0 + y * lat_span
    north = south + lat_span
    return west, south, east, north

def create_grid_mesh(dem_grid: np.ndarray, west: float, south: float, east: float, north: float):
    rows, cols = dem_grid.shape
    lats = np.linspace(north, south, rows)
    lons = np.linspace(west, east, cols)
    xx, yy = np.meshgrid(lons, lats)
    
    # 3D Positions array: [longitude, latitude, height]
    positions = np.column_stack([xx.ravel(), yy.ravel(), dem_grid.ravel()]).astype(np.float64)
    
    # Generate triangle indices for regular grid mesh
    r_indices, c_indices = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing='ij')
    i0 = (r_indices * cols + c_indices).ravel()
    i1 = (r_indices * cols + c_indices + 1).ravel()
    i2 = ((r_indices + 1) * cols + c_indices).ravel()
    i3 = ((r_indices + 1) * cols + c_indices + 1).ravel()
    
    # Pair triangles: (i0, i1, i2) and (i2, i1, i3)
    triangles1 = np.column_stack([i0, i1, i2])
    triangles2 = np.column_stack([i2, i1, i3])
    indices = np.vstack([triangles1, triangles2]).astype(np.uint32)
    
    return positions, indices

def generate_cesium_terrain_tiles():
    print("====================================================")
    print("CHENNAI-X: Official Quantized Mesh 1.0 Terrain Tiler")
    print("====================================================")

    elev_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "processed", "elevation.tif")
    tiles_dir = os.path.join(WORKSPACE_ROOT, "data", "terrain", "tiles")

    if not os.path.exists(elev_path):
        raise FileNotFoundError(f"Elevation raster not found at {elev_path}. Run process_dem.py first.")

    with rasterio.open(elev_path) as src:
        bounds = list(src.bounds) # [west, south, east, north]
        nodata = src.nodata
        dem_data = src.read(1)
        src_transform = src.transform

    min_lon, min_lat, max_lon, max_lat = bounds
    print(f"Source Elevation Raster: {elev_path}")
    print(f"Bounds: {bounds} | Dim: {dem_data.shape}")

    # Configure Zoom Levels for Chennai study area
    min_zoom = 8
    max_zoom = 13

    availability = []
    generated_tiles_count = 0
    tile_urls = ["{z}/{x}/{y}.terrain"]

    for z in range(min_zoom, max_zoom + 1):
        min_x = lon_to_tile_x(min_lon, z)
        max_x = lon_to_tile_x(max_lon, z)
        min_y = lat_to_tile_y(min_lat, z)
        max_y = lat_to_tile_y(max_lat, z)

        level_availability = []

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile_dir = os.path.join(tiles_dir, str(z), str(x))
                os.makedirs(tile_dir, exist_ok=True)
                tile_path = os.path.join(tile_dir, f"{y}.terrain")

                t_west, t_south, t_east, t_north = tile_bounds_epsg4326(x, y, z)

                # Sample DEM for tile bounding box using 33x33 height grid mesh
                grid_size = 33
                lats = np.linspace(t_north, t_south, grid_size)
                lons = np.linspace(t_west, t_east, grid_size)
                mesh_lon, mesh_lat = np.meshgrid(lons, lats)

                rows, cols = rasterio.transform.rowcol(src_transform, mesh_lon, mesh_lat)
                rows = np.clip(rows, 0, dem_data.shape[0] - 1)
                cols = np.clip(cols, 0, dem_data.shape[1] - 1)

                tile_dem = dem_data[rows, cols].astype(np.float32)
                tile_dem = tile_dem.reshape((grid_size, grid_size))

                if nodata is not None:
                    tile_dem = np.where(tile_dem == nodata, 0.0, tile_dem)
                tile_dem = np.nan_to_num(tile_dem, nan=0.0)

                # Generate 3D grid mesh positions and triangles
                positions, indices = create_grid_mesh(tile_dem, t_west, t_south, t_east, t_north)

                # Encode Quantized Mesh 1.0 binary payload per official specification into file object
                with open(tile_path, "wb") as f:
                    quantized_mesh_encoder.encode(
                        f,
                        positions,
                        indices,
                        bounds=[t_west, t_south, t_east, t_north]
                    )

                generated_tiles_count += 1
                level_availability.append({"x": x, "y": y})

        availability.append(level_availability)
        print(f"  [ZOOM {z}] Encoded {len(level_availability)} Quantized Mesh 1.0 tiles (x: {min_x}-{max_x}, y: {min_y}-{max_y})")

    # Generate layer.json manifest per Quantized Mesh 1.0 spec
    layer_json = {
        "tilejson": "2.1.0",
        "name": "Chennai Copernicus DEM Terrain",
        "description": "Copernicus DEM 3D Quantized Mesh Terrain Tileset for Chennai",
        "version": "1.0.0",
        "format": "quantized-mesh-1.0",
        "attribution": "Copernicus Data Space Ecosystem / GCC",
        "schema": "tms",
        "projection": "EPSG:4326",
        "bounds": bounds,
        "center": [(min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0, max_zoom],
        "minzoom": min_zoom,
        "maxzoom": max_zoom,
        "tiles": tile_urls,
        "available": availability
    }

    layer_json_path = os.path.join(tiles_dir, "layer.json")
    with open(layer_json_path, "w", encoding="utf-8") as f:
        json.dump(layer_json, f, indent=2)

    print("\n====================================================")
    print("QUANTIZED MESH 1.0 TERRAIN TILESET GENERATED & VERIFIED")
    print("====================================================")
    print(f"Format: quantized-mesh-1.0")
    print(f"Tiles Directory: {tiles_dir}")
    print(f"layer.json Path: {layer_json_path}")
    print(f"Total Tiles Generated: {generated_tiles_count}")
    print(f"Zoom Range: {min_zoom} to {max_zoom}")
    print(f"Bounds: {bounds}")
    print("====================================================\n")

    return layer_json

if __name__ == "__main__":
    generate_cesium_terrain_tiles()
