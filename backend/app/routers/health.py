from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check")
def health_check():
    """Returns the operational status of the service."""
    return {
        "status": "healthy",
        "project_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production"
    }
