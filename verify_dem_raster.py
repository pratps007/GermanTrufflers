import os
import sys
import numpy as np
import rasterio

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def verify_dem_raster():
    elev_path = os.path.join(WORKSPACE_ROOT, "data", "terrain", "processed", "elevation.tif")
    print("====================================================")
    print("CHENNAI-X: Phase 1 DEM Raster Hard Verification")
    print("====================================================")
    print(f"Target Elevation Raster: {elev_path}")

    if not os.path.exists(elev_path):
        print(f"[ERROR] Elevation raster not found at {elev_path}")
        sys.exit(1)

    with rasterio.open(elev_path) as src:
        crs = str(src.crs)
        bounds = list(src.bounds)
        width = src.width
        height = src.height
        nodata = src.nodata
        data = src.read(1)

    # Filter valid pixels
    if nodata is not None:
        valid_mask = (data != nodata) & (~np.isnan(data))
    else:
        valid_mask = ~np.isnan(data)

    valid_pixels = data[valid_mask]
    valid_count = len(valid_pixels)

    if valid_count == 0:
        print("[CRITICAL ERROR] 0 valid pixels in elevation raster! STOPPING.")
        sys.exit(1)

    min_val = float(np.min(valid_pixels))
    max_val = float(np.max(valid_pixels))
    mean_val = float(np.mean(valid_pixels))
    std_dev = float(np.std(valid_pixels))

    p10 = float(np.percentile(valid_pixels, 10))
    p50 = float(np.percentile(valid_pixels, 50))
    p90 = float(np.percentile(valid_pixels, 90))

    print("\n--- DEM RASTER METRICS ---")
    print(f"CRS: {crs}")
    print(f"Bounds: {bounds}")
    print(f"Dimensions: {width} x {height} ({width * height} total pixels)")
    print(f"Valid Pixels: {valid_count}")
    print(f"Min Elevation: {min_val:.2f} m")
    print(f"Max Elevation: {max_val:.2f} m")
    print(f"Mean Elevation: {mean_val:.2f} m")
    print(f"Standard Deviation: {std_dev:.2f} m")
    print(f"p10: {p10:.2f} m")
    print(f"p50: {p50:.2f} m")
    print(f"p90: {p90:.2f} m")
    print("--------------------------\n")

    # Hard Validation Checks
    if valid_count <= 0:
        print("[FAIL] Valid pixel count must be > 0.")
        sys.exit(1)

    if std_dev <= 0:
        print("[FAIL] Standard deviation must be > 0. DEM is flat/constant.")
        sys.exit(1)

    if min_val >= max_val:
        print("[FAIL] Min elevation must be < max elevation.")
        sys.exit(1)

    print("[SUCCESS] DEM raster contains non-constant physical elevation variation.")
    print("====================================================\n")

    return {
        "crs": crs,
        "bounds": bounds,
        "width": width,
        "height": height,
        "valid_pixels": valid_count,
        "min": min_val,
        "max": max_val,
        "mean": mean_val,
        "std_dev": std_dev,
        "p10": p10,
        "p50": p50,
        "p90": p90
    }

if __name__ == "__main__":
    verify_dem_raster()
