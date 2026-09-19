import os
import sys
import geopandas as gpd
from sqlalchemy import create_engine
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.data_sources.gcc_sources import GCC_DATASET_REGISTRY

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(WORKSPACE_ROOT, "backend", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://chennaix_user:chennaix_password@localhost:5432/chennaix"
)

def load_processed_layers_to_postgis():
    """
    Imports processed GeoJSON layers from data/ into PostGIS tables.
    """
    print("====================================================")
    print("CHENNAI-X: PostGIS Spatial Database Layer Import")
    print("====================================================")
    print(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Successfully connected to PostgreSQL/PostGIS database.")
    except Exception as e:
        print(f"[SKIP] PostGIS connection not available: {e}")
        print("Processed GeoJSON files are saved and ready for database import when PostGIS container starts.")
        return

    for ds in GCC_DATASET_REGISTRY:
        table_name = f"gcc_{ds['id']}"
        proc_path = os.path.join(WORKSPACE_ROOT, ds['processed_destination'])

        if not os.path.exists(proc_path):
            print(f"[SKIP] {ds['id']}: Processed GeoJSON not found at {proc_path}")
            continue

        try:
            print(f"\n[LOADING] {ds['name']} -> PostGIS table '{table_name}'")
            gdf = gpd.read_file(proc_path)
            
            # PostGIS expects clean column names
            gdf.columns = [c.lower().replace(" ", "_").replace("-", "_") for c in gdf.columns]
            
            # Load to PostGIS
            gdf.to_postgis(
                name=table_name,
                con=engine,
                if_exists="replace",
                index=True,
                index_label="id",
                schema="public",
                chunksize=1000
            )
            print(f"  [SUCCESS] Inserted {len(gdf)} records into table '{table_name}'.")
        except Exception as e:
            print(f"  [ERROR] Failed to load {table_name}: {e}")

if __name__ == "__main__":
    load_processed_layers_to_postgis()
