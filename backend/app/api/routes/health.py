from typing import Dict
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=Dict[str, str], status_code=200)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify backend foundation is running.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
