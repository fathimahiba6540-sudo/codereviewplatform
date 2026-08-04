import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.exceptions import AppException, app_exception_handler
from backend.app.middleware.logging_middleware import LoggingMiddleware
from backend.app.routers import health, auth, users, projects, ingestion
from backend.app.database.init_db import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Full-Stack AI-Powered Multi-Agent Code Review Platform API",
    version="1.0.0"
)

# Custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)

# Custom logging and request tracking middleware
app.add_middleware(LoggingMiddleware)

# Configure CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(ingestion.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def startup_event():
    """Ensure required directories exist and initialize database on startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    try:
        init_db()
    except Exception as e:
        print(f"Startup DB init notice: {e}")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
