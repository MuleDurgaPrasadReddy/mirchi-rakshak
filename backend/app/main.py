from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Backend Foundation for MirchiRakshak AI Crop Pathology & Farming Assistance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to MirchiRakshak AI API",
        "docs": "/docs",
        "health": "/api/health",
    }
