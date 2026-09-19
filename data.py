from fastapi import APIRouter
from app.services.data_registry import data_registry

router = APIRouter()

@router.get("/data/catalog")
async def get_data_catalog():
    """
    Returns the central data catalog containing all ingested, available, and modelled datasets with strict provenance tags.
    """
    return {
        "status": "success",
        "platform": "PRAVAH-X",
        "total_datasets": len(data_registry.get_catalog()),
        "catalog": data_registry.get_catalog()
    }
