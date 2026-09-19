from fastapi import APIRouter
from app.api.v1.endpoints import health, geospatial, simulation, response, data, agriculture, event

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(geospatial.router, tags=["Geospatial"])
api_router.include_router(simulation.router, tags=["Simulation"])
api_router.include_router(response.router, tags=["Response Orchestrator"])
api_router.include_router(data.router, tags=["Data Provenance Catalog"])
api_router.include_router(agriculture.router, tags=["Agriculture Intelligence"])
api_router.include_router(event.router, tags=["Multi-Hazard Event Graph & What-If"])
