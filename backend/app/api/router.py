from fastapi import APIRouter
from app.api.routes import health, profile, farms, scans, analysis, chat

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(farms.router)
api_router.include_router(scans.router)
api_router.include_router(analysis.router)
api_router.include_router(chat.router)
