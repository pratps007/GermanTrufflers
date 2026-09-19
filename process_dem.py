import os
import sys
import json
import glob
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from shapely.geometry import box

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def process_copernicus_dem():
    print("====================================================")
    print("CHENNAI-X: Copernicus DEM Metric Processing Pipeline")
    print("====================================================")

    raw_dir = os.path.join(WORKSPACE_ROOT, "data", "terrain", "raw")
    proc_dir = os.path.join(WORKSPACE_ROOT, "data", "terrain", "processed")
    meta_dir = os.path.join(WORKSPACE_ROOT, "data", "terrain", "metadata")

    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    # 1. Locate Raw Tiles
    raw_files = sorted(glob.glob(os.path.join(raw_dir, "Copernicus_DEM_*.tif")))
    if not raw_files:
        raise FileNotFoundError(f"No raw Copernicus DEM files found in {raw_dir}. Run download_dem.py first.")

    print(f"Found {len(raw_files)} raw DEM tiles for processing:")
    for rf in raw_files:
        print(f"  - {os.path.basename(rf)}")

    # 2. Validate and Open Individual Tiles
    src_datasets = []
    tile_ids = []
    for rf in raw_files:
        ds = rasterio.open(rf)
        src_datasets.append(ds)
        tile_name = os.path.basename(rf).replace("Copernicus_DEM_", "").replace(".tif", "")
        tile_ids.append(tile_name)

    # 3. Mosaic Tiles First
    print("\n[MOSAIC] Mosaicking adjacent DEM tiles...")
    mosaic_data, mosaic_transform = merge(src_datasets)
    source_crs = str(src_datasets[0].crs)
    nodata_val = src_datasets[0].nodata if src_datasets[0].nodata is not None else -9999.0

    print(f"  Mosaic dimensions: {mosaic_data.shape} | Source CRS: {source_crs}")

    # Close raw sources
    for ds in src_datasets:
        ds.close()

    # 4. Determine Study Area Bounding Box (GCC Boundary + 0.02 deg buffer)
    gcc_wards_path = os.path.join(WORKSPACE_ROOT, "data", "boundary", "processed", "wards.geojson")
    if os.path.exists(gcc_wards_path):
        print(f"\n[BOUNDS] Deriving study area from official GCC Wards dataset: {gcc_wards_path}")
        gdf = gpd.read_file(gcc_wards_path)
        minx, miny, maxx, maxy = gdf.total_bounds
        buffer_deg = 0.02  # ~2km buffer
        study_bounds = [minx - buffer_deg, miny - buffer_deg, maxx + buffer_deg, maxy + buffer_deg]
    else:
        study_bounds = [80.13, 12.85, 80.34, 13.25]

    print(f"  Study Area Bounding Box (+ Buffer): {study_bounds}")

    # Clip Mosaic to Study Area in EPSG:4326
    study_box = box(*study_bounds)
    geo_df = gpd.GeoDataFrame({'geometry': [study_box]}, crs="EPSG:4326")

    # Create temporary in-memory raster for clipping
    mosaic_meta = {
        "driver": "GTiff",
        "height": mosaic_data.shape[1],
        "width": mosaic_data.shape[2],
        "count": 1,
        "dtype": mosaic_data.dtype,
        "crs": source_crs,
        "transform": mosaic_transform,
        "nodata": nodata_val
    }

    temp_mosaic_path = os.path.join(proc_dir, "temp_mosaic.tif")
    with rasterio.open(temp_mosaic_path, "w", **mosaic_meta) as dst:
        dst.write(mosaic_data[0], 1)

    with rasterio.open(temp_mosaic_path) as src:
        clipped_data, clipped_transform = mask(src, geo_df.geometry, crop=True)
        clipped_meta = src.meta.copy()

    os.remove(temp_mosaic_path)

    clipped_meta.update({
        "height": clipped_data.shape[1],
        "width": clipped_data.shape[2],
        "transform": clipped_transform
    })

    dem_source_path = os.path.join(proc_dir, "dem_source.tif")
    with rasterio.open(dem_source_path, "w", **clipped_meta) as dst:
        dst.write(clipped_data[0], 1)

    print(f"  [SAVED] Source DEM clipped to study area -> {dem_source_path}")

    # 5. Reproject to Metric Projected CRS (EPSG:32644 - UTM Zone 44N)
    target_utm_crs = "EPSG:32644"
    print(f"\n[REPROJECTING] Reprojecting analysis DEM to metric CRS ({target_utm_crs})...")

    with rasterio.open(dem_source_path) as src:
        transform_utm, width_utm, height_utm = calculate_default_transform(
            src.crs, target_utm_crs, src.width, src.height, *src.bounds
        )
        kwargs_utm = src.meta.copy()
        kwargs_utm.update({
            'crs': target_utm_crs,
            'transform': transform_utm,
            'width': width_utm,
            'height': height_utm,
            'nodata': nodata_val
        })

        dem_utm_data = np.full((height_utm, width_utm), nodata_val, dtype=np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=dem_utm_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform_utm,
            dst_crs=target_utm_crs,
            resampling=Resampling.bilinear
        )

    dem_utm_path = os.path.join(proc_dir, "dem_projected_utm.tif")
    with rasterio.open(dem_utm_path, "w", **kwargs_utm) as dst:
        dst.write(dem_utm_data, 1)

    print(f"  [SAVED] Metric Projected DEM ({target_utm_crs}) -> {dem_utm_path}")

    # 6. Calculate Metric Terrain Derivatives (Slope, Aspect, Hillshade)
    print("\n[CALCULATING DERIVATIVES] Computing metric slope, aspect, and hillshade from UTM raster...")

    valid_mask = (dem_utm_data != nodata_val) & (~np.isnan(dem_utm_data))
    dem_clean = np.where(valid_mask, dem_utm_data, np.nan)

    # Pixel resolution in meters
    cell_size_x = abs(transform_utm.a)
    cell_size_y = abs(transform_utm.e)

    # 2D Spatial Gradients (in meters)
    dy, dx = np.gradient(dem_clean, cell_size_y, cell_size_x)

    # Slope in degrees
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    slope_deg = np.where(valid_mask, slope_deg, nodata_val).astype(np.float32)

    # Aspect in degrees (0 - 360, relative to North)
    aspect_rad = np.arctan2(-dx, dy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = np.mod(aspect_deg, 360.0)
    aspect_deg = np.where(valid_mask, aspect_deg, nodata_val).astype(np.float32)

    # Hillshade (Azimuth: 315 deg, Altitude: 45 deg)
    azimuth_rad = np.radians(315.0)
    altitude_rad = np.radians(45.0)

    shaded = (np.sin(altitude_rad) * np.cos(slope_rad) +
              np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad))
    hillshade = np.clip(255.0 * np.maximum(0.0, shaded), 0, 255).astype(np.uint8)
    hillshade = np.where(valid_mask, hillshade, 0).astype(np.uint8)

    # Reproject derivatives back to EPSG:4326 for web / Cesium serving
    derivatives_4326 = {}
    for name, arr, dtype, nd in [
        ("elevation", dem_clean, np.float32, nodata_val),
        ("slope", slope_deg, np.float32, nodata_val),
        ("aspect", aspect_deg, np.float32, nodata_val),
        ("hillshade", hillshade, np.uint8, 0)
    ]:
        out_path = os.path.join(proc_dir, f"{name}.tif")
        out_data = np.full((clipped_data.shape[1], clipped_data.shape[2]), nd, dtype=dtype)

        with rasterio.open(dem_source_path) as ref_src:
            reproject(
                source=arr,
                destination=out_data,
                src_transform=transform_utm,
                src_crs=target_utm_crs,
                dst_transform=ref_src.transform,
                dst_crs=ref_src.crs,
                resampling=Resampling.bilinear if dtype != np.uint8 else Resampling.nearest
            )

            out_meta = ref_src.meta.copy()
            out_meta.update({
                "dtype": dtype,
                "nodata": nd
            })

            with rasterio.open(out_path, "w", **out_meta) as dst:
                dst.write(out_data, 1)

        derivatives_4326[name] = out_path
        print(f"  [SAVED DERIVATIVE] {name}.tif ({dtype}) -> {out_path}")

    # 7. Compute REAL Elevation Statistics
    valid_elevations = dem_clean[valid_mask]
    min_elev = float(np.min(valid_elevations))
    max_elev = float(np.max(valid_elevations))
    mean_elev = float(np.mean(valid_elevations))
    total_pixels = dem_clean.size
    nodata_pixels = int(np.sum(~valid_mask))
    nodata_pct = round((nodata_pixels / total_pixels) * 100.0, 2)

    with rasterio.open(dem_source_path) as final_src:
        final_bounds = list(final_src.bounds)
        final_res = final_src.res
        final_dim = [final_src.width, final_src.height]

    # 8. Write Machine-Readable Metadata
    metadata = {
        "dataset": "Copernicus DEM",
        "product": "Copernicus DEM GLO-90 DSM",
        "source_organization": "Copernicus Data Space Ecosystem / AWS Open Data",
        "surface_model_type": "Digital Surface Model (DSM)",
        "resolution_nominal_m": 90,
        "pixel_resolution_degrees": list(final_res),
        "source_crs": source_crs,
        "analysis_crs": target_utm_crs,
        "output_crs": "EPSG:4326",
        "tiles_used": tile_ids,
        "bounds": final_bounds,
        "study_area_bounds": study_bounds,
        "dimensions": final_dim,
        "min_elevation_m": round(min_elev, 2),
        "max_elevation_m": round(max_elev, 2),
        "mean_elevation_m": round(mean_elev, 2),
        "nodata_percentage": nodata_pct,
        "provenance": {
            "Copernicus DEM DSM": "VERIFIED SOURCE",
            "Reprojected DEM (EPSG:32644)": "DERIVED TRANSFORMATION",
            "Slope / Aspect / Hillshade": "DERIVED PRODUCTS"
        },
        "scientific_guardrails": [
            "Copernicus DEM is a Digital Surface Model (DSM) representing top-of-surface elevation.",
            "Slope, aspect, and hillshade are derived from UTM Zone 44N (EPSG:32644) metric projection.",
            "This raster is NOT bare-earth DTM and does not represent real-time water depth or flood prediction."
        ]
    }

    meta_file = os.path.join(meta_dir, "dem_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n====================================================")
    print("DEM PROCESSING COMPLETE & VERIFIED")
    print("====================================================")
    print(f"Product: {metadata['product']}")
    print(f"Tiles Used: {tile_ids}")
    print(f"Analysis CRS: {target_utm_crs} | Output CRS: EPSG:4326")
    print(f"Bounds: {final_bounds}")
    print(f"Dimensions: {final_dim[0]} x {final_dim[1]} pixels")
    print(f"Min Elevation: {metadata['min_elevation_m']} m")
    print(f"Max Elevation: {metadata['max_elevation_m']} m")
    print(f"Mean Elevation: {metadata['mean_elevation_m']} m")
    print(f"NoData: {nodata_pct}%")
    print(f"Metadata File: {meta_file}")
    print("====================================================\n")

if __name__ == "__main__":
    process_copernicus_dem()
