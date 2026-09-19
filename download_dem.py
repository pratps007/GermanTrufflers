import os
import sys
import math
import httpx
import rasterio
from typing import List, Dict, Any, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Default study area bounding box for Chennai (WEST, SOUTH, EAST, NORTH)
CHENNAI_BBOX = [80.13, 12.85, 80.34, 13.25]

def get_required_dem_tile_ids(bbox: List[float]) -> List[str]:
    """
    Given a bounding box [minx, miny, maxx, maxy] in WGS84,
    returns the list of 1°x1° Copernicus DEM tile identifiers.
    Example: [80.13, 12.85, 80.34, 13.25] -> ['N12_00_E080_00', 'N13_00_E080_00']
    """
    minx, miny, maxx, maxy = bbox
    
    min_lat = math.floor(miny)
    max_lat = math.floor(maxy) if math.floor(maxy) != maxy else math.floor(maxy) - 1
    min_lon = math.floor(minx)
    max_lon = math.floor(maxx) if math.floor(maxx) != maxx else math.floor(maxx) - 1
    
    tile_ids = []
    for lat in range(min_lat, max_lat + 1):
        for lon in range(min_lon, max_lon + 1):
            lat_str = f"N{abs(lat):02d}_00" if lat >= 0 else f"S{abs(lat):02d}_00"
            lon_str = f"E{abs(lon):03d}_00" if lon >= 0 else f"W{abs(lon):03d}_00"
            tile_ids.append(f"{lat_str}_{lon_str}")
            
    return tile_ids

def resolve_and_download_copernicus_tile(tile_id: str, resolution: int = 90) -> Tuple[str, Dict[str, Any]]:
    """
    Resolves official Copernicus DEM tile from public AWS distribution / Copernicus Data Space Ecosystem.
    Tries candidates for GLO-90 / GLO-30 resolution.
    """
    # Candidate URL naming patterns on public Copernicus DEM AWS buckets
    url_templates = []
    if resolution == 30:
        url_templates.extend([
            f"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{tile_id}_DEM/Copernicus_DSM_COG_10_{tile_id}_DEM.tif",
            f"https://copernicus-dem-30m.s3.amazonaws.com/COP30_{tile_id}_DEM/COP30_{tile_id}_DEM.tif",
            f"https://copernicus-dem-30m.s3.amazonaws.com/{tile_id}/{tile_id}.tif",
        ])
    
    # GLO-90 candidates
    url_templates.extend([
        f"https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_{tile_id}_DEM/Copernicus_DSM_COG_30_{tile_id}_DEM.tif",
        f"https://copernicus-dem-90m.s3.amazonaws.com/COP90_{tile_id}_DEM/COP90_{tile_id}_DEM.tif",
        f"https://copernicus-dem-90m.s3.amazonaws.com/{tile_id}/{tile_id}.tif",
        f"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{tile_id}_DEM/Copernicus_DSM_COG_10_{tile_id}_DEM.tif",
    ])

    raw_dir = os.path.join(WORKSPACE_ROOT, "data", "terrain", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    target_filepath = os.path.join(raw_dir, f"Copernicus_DEM_{tile_id}.tif")

    headers = {"User-Agent": "CHENNAI-X Emergency Digital Twin Terrain Pipeline/1.0"}

    print(f"[RESOLVING] Searching Copernicus DEM distribution for tile '{tile_id}'...")

    successful_url = None
    content_length = 0

    for url in url_templates:
        try:
            head_res = httpx.head(url, headers=headers, timeout=10.0, follow_redirects=True)
            if head_res.status_code == 200:
                successful_url = url
                content_length = int(head_res.headers.get("content-length", 0))
                break
        except Exception:
            continue

    if not successful_url:
        # Attempt GET directly if HEAD is disallowed by AWS S3 CORS
        for url in url_templates:
            try:
                with httpx.stream("GET", url, headers=headers, timeout=15.0, follow_redirects=True) as stream_res:
                    if stream_res.status_code == 200:
                        successful_url = url
                        content_length = int(stream_res.headers.get("content-length", 0))
                        break
            except Exception:
                continue

    if not successful_url:
        raise RuntimeError(
            f"FAILED to resolve tile '{tile_id}' from official Copernicus DEM AWS catalog. "
            f"Stopped to prevent constructing unverified or fake raster data."
        )

    print(f"  [FOUND] Resolved: {successful_url} ({round(content_length / (1024*1024), 2)} MB)")

    # Download tile
    print(f"  [DOWNLOADING] {target_filepath}...")
    with httpx.stream("GET", successful_url, headers=headers, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        with open(target_filepath, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=65536):
                f.write(chunk)

    # Validate raster file with rasterio
    with rasterio.open(target_filepath) as src:
        bounds = list(src.bounds)
        crs = str(src.crs)
        res = src.res
        width, height = src.width, src.height

    print(f"  [VALIDATED] Tile {tile_id} | CRS: {crs} | Res: {res} | Bounds: {bounds} | Dim: {width}x{height}")

    meta = {
        "tile_id": tile_id,
        "resolved_url": successful_url,
        "filepath": target_filepath,
        "content_length_bytes": content_length,
        "bounds": bounds,
        "crs": crs,
        "resolution": res,
        "dimensions": [width, height]
    }
    return target_filepath, meta

def main():
    print("====================================================")
    print("CHENNAI-X: Official Copernicus DEM Downloader")
    print("====================================================")

    res_env = os.getenv("DEM_RESOLUTION", "90")
    resolution = int(res_env)

    tile_ids = get_required_dem_tile_ids(CHENNAI_BBOX)
    print(f"Study Area Bounding Box: {CHENNAI_BBOX}")
    print(f"Intersecting 1°x1° Grid Cells Required: {tile_ids}")
    print(f"Requested Target Resolution: GLO-{resolution}")

    downloaded_tiles = []
    tile_metas = []

    for tile_id in tile_ids:
        try:
            filepath, meta = resolve_and_download_copernicus_tile(tile_id, resolution=resolution)
            downloaded_tiles.append(filepath)
            tile_metas.append(meta)
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Tile resolution failed for {tile_id}: {e}")
            print("STOPPING ingestion pipeline to avoid incomplete or synthetic coverage.")
            sys.exit(1)

    print("\n====================================================")
    print("DEM DOWNLOAD COMPLETE & VERIFIED")
    print("====================================================")
    print(f"Total Tiles Downloaded: {len(downloaded_tiles)}")
    for m in tile_metas:
        print(f"  - Tile: {m['tile_id']} | File: {m['filepath']} | Dim: {m['dimensions']}")
    print("====================================================\n")

if __name__ == "__main__":
    main()
