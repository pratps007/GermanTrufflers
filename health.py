from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint returning backend status, system info, and UTC timestamp.
    """
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "development"
    }
