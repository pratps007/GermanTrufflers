import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class DatasetMetadata(BaseModel):
    id: str
    name: str
    category: str  # ENVIRONMENT, CITY, PEOPLE, AGRICULTURE, RESPONSE, INTELLIGENCE, RECOVERY
    source: str
    source_url: str
    source_type: str  # OFFICIAL_GIS, SATELLITE_AGENCY, TELEMETRY, RESEARCH_INSTITUTE, MODELLED
    provenance: str  # VERIFIED, OBSERVED, MODELLED, SIMULATED
    status: str  # INGESTED, AVAILABLE, CONNECTOR_NOT_ACTIVE, MODELLED, SIMULATED, STALE, ERROR
    data_type: str  # VECTOR_POLYGON, VECTOR_LINE, RASTER_DEM, TELEMETRY_GRID, TABULAR
    coverage: str
    geometry_type: Optional[str] = None
    last_updated: str
    observed_at: Optional[str] = None
    forecast_period: Optional[str] = None
    confidence: str  # HIGH, MODERATE, ESTIMATED, EXPERIMENTAL

class DataRegistryService:
    def __init__(self):
        self._catalog: Dict[str, DatasetMetadata] = self._initialize_catalog()

    def _initialize_catalog(self) -> Dict[str, DatasetMetadata]:
        datasets = [
            DatasetMetadata(
                id="copernicus_dem_glo90",
                name="Copernicus DEM DSM 90m (UTM Zone 44N)",
                category="ENVIRONMENT",
                source="Copernicus / ESA / EUMETSAT",
                source_url="https://copernicus-dem-30m.s3.amazonaws.com/",
                source_type="SATELLITE_AGENCY",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="RASTER_DEM",
                coverage="Greater Chennai Region (UTM 44N)",
                geometry_type="Grid Elevation (m)",
                last_updated="2024-01-15",
                observed_at="2023-12-01",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_wards_200",
                name="GCC Ward Boundaries (200 Wards)",
                category="CITY",
                source="Greater Chennai Corporation (GCC) Official GIS",
                source_url="https://chennaicorporation.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_POLYGON",
                coverage="200 Municipal Wards",
                geometry_type="MultiPolygon",
                last_updated="2024-02-01",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_zones_15",
                name="GCC Zone Boundaries (15 Administrative Zones)",
                category="CITY",
                source="Greater Chennai Corporation (GCC) Official GIS",
                source_url="https://chennaicorporation.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_POLYGON",
                coverage="15 Municipal Zones",
                geometry_type="MultiPolygon",
                last_updated="2024-02-01",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_rivers_canals",
                name="GCC Hydrological Network (Adyar, Cooum & Buckingham Canal)",
                category="ENVIRONMENT",
                source="GCC Hydrographic Survey & PWD Water Resources Dept",
                source_url="https://www.wrd.tn.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_POLYGON",
                coverage="Adyar River, Cooum River, Buckingham Canal",
                geometry_type="Polygon",
                last_updated="2023-11-20",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_stormwater_drains",
                name="GCC Stormwater Drain Conduits (11,500 Segments)",
                category="CITY",
                source="GCC Storm Water Drain (SWD) Department",
                source_url="https://chennaicorporation.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_LINE",
                coverage="11,500 Drain Conduits Across 15 Zones",
                geometry_type="LineString",
                last_updated="2024-01-10",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_road_network",
                name="GCC Street Transport Network (37,300 Edges)",
                category="CITY",
                source="GCC Highways & Bus Route Roads Department",
                source_url="https://chennaicorporation.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_LINE",
                coverage="37,300 Road Edges & Intersection Nodes",
                geometry_type="LineString",
                last_updated="2024-02-15",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="gcc_subways",
                name="GCC Vehicular Subways & Underpasses (28 Subways)",
                category="CITY",
                source="GCC Bridges & Subways Division",
                source_url="https://chennaicorporation.gov.in/",
                source_type="OFFICIAL_GIS",
                provenance="VERIFIED",
                status="INGESTED",
                data_type="VECTOR_POLYGON",
                coverage="28 Vulnerable Vehicular Subways",
                geometry_type="Polygon",
                last_updated="2023-10-30",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="imd_aws_telemetry",
                name="IMD AWS Rain Gauge & Telemetry Feed",
                category="ENVIRONMENT",
                source="India Meteorological Department (IMD) / SACHET NDMA",
                source_url="https://mausam.imd.gov.in/",
                source_type="TELEMETRY",
                provenance="OBSERVED",
                status="CONNECTOR_NOT_ACTIVE",
                data_type="TELEMETRY_GRID",
                coverage="Tamil Nadu Rain Gauge Telemetry Network",
                geometry_type="Point",
                last_updated="2026-09-19",
                forecast_period="24 Hours",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="icar_crida_agro_contingency",
                name="ICAR-CRIDA District Agriculture Contingency Plans",
                category="AGRICULTURE",
                source="ICAR-CRIDA / Tamil Nadu Agricultural University (TNAU)",
                source_url="http://www.crida.in/",
                source_type="RESEARCH_INSTITUTE",
                provenance="VERIFIED",
                status="AVAILABLE",
                data_type="TABULAR",
                coverage="Kanchipuram, Tiruvallur & Chengalpattu Districts",
                last_updated="2024-01-01",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="isro_bhuvan_flood_2015",
                name="ISRO/Bhuvan Historical Satellite Flood Inundation (2015 Event)",
                category="ENVIRONMENT",
                source="NRSC / ISRO Bhuvan Disaster Services",
                source_url="https://bhuvan-app1.nrsc.gov.in/disaster/",
                source_type="SATELLITE_AGENCY",
                provenance="OBSERVED",
                status="AVAILABLE",
                data_type="VECTOR_POLYGON",
                coverage="Chennai Metropolitan Area 2015 Inundation",
                geometry_type="MultiPolygon",
                last_updated="2015-12-08",
                observed_at="2015-12-05",
                confidence="HIGH"
            ),
            DatasetMetadata(
                id="modelled_hydro_inundation",
                name="2D Hydrodynamic Surface Inundation Model",
                category="INTELLIGENCE",
                source="PRAVAH-X Hydrodynamic Engine",
                source_url="http://localhost:8000/api/v1/simulation/run",
                source_type="MODELLED",
                provenance="MODELLED",
                status="MODELLED",
                data_type="VECTOR_POLYGON",
                coverage="Modelled Inundation Depth & Susceptibility Grids",
                geometry_type="MultiPolygon",
                last_updated="2026-09-19",
                confidence="ESTIMATED"
            ),
            DatasetMetadata(
                id="simulated_response_fleet",
                name="Simulated Emergency Fleet Units (A01-F02)",
                category="RESPONSE",
                source="PRAVAH-X Dispatch Synthetic Hubs",
                source_url="http://localhost:8000/api/v1/response/plan",
                source_type="MODELLED",
                provenance="SIMULATED",
                status="SIMULATED",
                data_type="TABULAR",
                coverage="6 Synthetic Emergency Units (Ambulance, Rescue, Fire)",
                geometry_type="Point",
                last_updated="2026-09-19",
                confidence="EXPERIMENTAL"
            )
        ]
        return {d.id: d for d in datasets}

    def get_catalog(self) -> List[Dict[str, Any]]:
        return [dataset.model_dump() for dataset in self._catalog.values()]

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = self._catalog.get(dataset_id)
        return dataset.model_dump() if dataset else None

data_registry = DataRegistryService()
