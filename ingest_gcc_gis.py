import os
import sys
import json
import shutil
import time
from datetime import datetime, timezone
import httpx
import geopandas as gpd
from shapely.geometry import shape

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.data_sources.gcc_sources import GCC_DATASET_REGISTRY

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def resolve_path(relative_path: str) -> str:
  return os.path.join(WORKSPACE_ROOT, relative_path)


def fetch_arcgis_layer_geojson(
    service_url: str, batch_size: int = 1000
) -> tuple[dict, int]:
  """Queries ArcGIS REST service endpoint with pagination to retrieve all features as GeoJSON."""
  query_url = f'{service_url.rstrip("/")}/query'
  all_features = []
  result_offset = 0
  exceeded_transfer_limit = True

  headers = {'User-Agent': 'CHENNAI-X Emergency Digital Twin Ingestion Pipeline/1.0'}

  metadata = {}

  # Attempt initial metadata query if needed
  try:
    meta_res = httpx.get(
        f'{service_url.rstrip("/")}?f=json', headers=headers, timeout=15.0, verify=False
    )
    if meta_res.status_code == 200:
      metadata = meta_res.json()
  except Exception:
    pass

  while exceeded_transfer_limit:
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'outSR': '4326',  # Request reprojected WGS84 directly from ArcGIS REST
        'resultOffset': result_offset,
        'resultRecordCount': batch_size,
    }

    response = httpx.get(
        query_url, params=params, headers=headers, timeout=60.0, verify=False
    )
    response.raise_for_status()
    data = response.json()

    if 'error' in data:
      raise ValueError(f"ArcGIS REST Error: {data['error']}")

    features = data.get('features', [])
    if not features:
      break

    all_features.extend(features)

    # Check pagination metadata
    exceeded_transfer_limit = data.get('exceededTransferLimit', False)
    if len(features) < batch_size:
      exceeded_transfer_limit = False

    result_offset += len(features)
    time.sleep(0.1)  # Respectful query interval

  combined_geojson = {
      'type': 'FeatureCollection',
      'features': all_features,
      'metadata': {
          'retrieved_at': datetime.now(timezone.utc).isoformat(),
          'feature_count': len(all_features),
          'arcgis_metadata': metadata.get('name', ''),
      },
  }

  return combined_geojson, len(all_features)


def process_dataset(ds: dict) -> dict:
  """Fetch, validate, reproject, and store dataset based on registry definition."""
  dataset_id = ds['id']
  name = ds['name']
  service_url = ds['service_url']
  raw_path = resolve_path(ds['raw_destination'])
  proc_path = resolve_path(ds['processed_destination'])
  source_crs = ds['source_crs']
  target_crs = ds['target_crs']

  os.makedirs(os.path.dirname(raw_path), exist_ok=True)
  os.makedirs(os.path.dirname(proc_path), exist_ok=True)

  print(f"\n[INGESTING] {name} ({dataset_id})")
  print(f"  URL: {service_url}")

  start_time = time.time()

  try:
    # 1. Fetch from ArcGIS REST
    raw_geojson, feature_count = fetch_arcgis_layer_geojson(service_url)

    # 2. Save Raw JSON
    with open(raw_path, 'w', encoding='utf-8') as f:
      json.dump(raw_geojson, f, indent=2)

    if feature_count == 0:
      print(f"  [WARNING] 0 features returned for {dataset_id}")
      return {
          'id': dataset_id,
          'name': name,
          'status': 'EMPTY',
          'features': 0,
          'geometry_types': [],
          'source_crs': source_crs,
          'output_crs': target_crs,
          'path': proc_path,
          'error': 'Zero features returned',
      }

    # 3. Read into GeoPandas & Validate
    gdf = gpd.GeoDataFrame.from_features(raw_geojson['features'])

    # Set CRS if missing
    if gdf.crs is None:
      gdf.set_crs(epsg=4326, inplace=True)

    # If native geometry was not reprojected by ArcGIS, reproject explicitly
    if gdf.crs.to_epsg() != 4326:
      gdf = gdf.to_crs(epsg=4326)

    # Geometry validation & cleanup
    invalid_count = (~gdf.is_valid).sum()
    empty_count = gdf.is_empty.sum()
    if invalid_count > 0:
      print(f'  [FIXING] Repairing {invalid_count} invalid geometries...')
      gdf['geometry'] = gdf.geometry.make_valid()

    if empty_count > 0:
      print(f'  [CLEANING] Removing {empty_count} empty geometries...')
      gdf = gdf[~gdf.is_empty]

    geometry_types = list(gdf.geometry.type.unique())
    total_bounds = list(gdf.total_bounds)  # [minx, miny, maxx, maxy]

    # 4. Save Processed GeoJSON
    gdf.to_file(proc_path, driver='GeoJSON')
    print(f'  [SAVED] Processed GeoJSON ({len(gdf)} features) -> {proc_path}')

    # 5. Optional Copy to Frontend Public (for lightweight boundary layers like Wards/Zones)
    if 'frontend_public_copy' in ds:
      pub_path = resolve_path(ds['frontend_public_copy'])
      os.makedirs(os.path.dirname(pub_path), exist_ok=True)
      shutil.copy2(proc_path, pub_path)
      print(f'  [COPIED] Frontend public asset -> {pub_path}')

    duration = round(time.time() - start_time, 2)
    print(
        f'  [SUCCESS] Ingested in {duration}s. Geometries: {geometry_types}. Bounding Box: {total_bounds}'
    )

    return {
        'id': dataset_id,
        'name': name,
        'status': 'SUCCESS',
        'features': len(gdf),
        'geometry_types': [str(gt) for gt in geometry_types],
        'bounds': total_bounds,
        'source_crs': source_crs,
        'output_crs': target_crs,
        'path': proc_path,
        'provenance': ds['provenance_classification'],
        'duration_seconds': duration,
    }

  except Exception as e:
    duration = round(time.time() - start_time, 2)
    print(f'  [FAILED] {dataset_id}: {str(e)}')
    return {
        'id': dataset_id,
        'name': name,
        'status': 'FAILED',
        'features': 0,
        'source_crs': source_crs,
        'output_crs': target_crs,
        'path': proc_path,
        'error': str(e),
        'duration_seconds': duration,
    }


def main():
  print('====================================================')
  print('CHENNAI-X: Official GCC GIS Data Ingestion Pipeline')
  print('====================================================')

  results = []
  for ds in GCC_DATASET_REGISTRY:
    res = process_dataset(ds)
    results.append(res)

  # Generate Ingestion Report
  report_path = resolve_path('data/ingestion_report.json')
  report_data = {
      'ingested_at': datetime.now(timezone.utc).isoformat(),
      'datasets': results,
  }
  with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2)

  print('\n====================================================')
  print('INGESTION SUMMARY REPORT')
  print('====================================================')
  print(
      f'{"DATASET ID":<20} | {"STATUS":<8} | {"COUNT":<8} | {"GEOMETRY TYPE":<20}'
  )
  print('----------------------------------------------------')
  for r in results:
    geom_str = ', '.join(r.get('geometry_types', [])) or '—'
    print(
        f"{r['id']:<20} | {r['status']:<8} | {r['features']:<8} |"
        f' {geom_str:<20}'
    )
  print('====================================================\n')


if __name__ == '__main__':
  main()
