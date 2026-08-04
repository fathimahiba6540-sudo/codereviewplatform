"""
ingestion.py — Phase 4 API Router
Endpoints for triggering and monitoring the code ingestion pipeline.
"""
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.routers.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.services.ingestion_service import IngestionService
from backend.app.models.schemas import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post(
    "/projects/{project_id}/ingest",
    response_model=APIResponse,
    summary="Trigger code ingestion pipeline",
    description=(
        "Starts the Phase 4 ingestion pipeline for a project: "
        "parses files, chunks source code, and vectorizes into ChromaDB. "
        "Can be run as a background task or synchronously."
    ),
)
def trigger_ingestion(
    project_id: str,
    background_tasks: BackgroundTasks,
    run_async: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger ingestion for a specific project.

    - **run_async=true** (default): queues ingestion as a background task, returns immediately.
    - **run_async=false**: runs ingestion synchronously and returns final result.
    """
    user_id = str(current_user.id)

    if run_async:
        # Queue ingestion as a background task so the HTTP response returns immediately
        background_tasks.add_task(
            _run_ingestion_background,
            project_id=project_id,
            user_id=user_id,
        )
        return APIResponse(
            success=True,
            message="Ingestion pipeline started in background. Poll /ingestion/projects/{id}/status for updates.",
            data={"project_id": project_id, "queued": True},
        )
    else:
        # Synchronous run — useful for testing and small projects
        try:
            project = IngestionService.ingest_project(db, project_id, user_id)
            return APIResponse(
                success=True,
                message="Ingestion completed successfully.",
                data={
                    "project_id": project_id,
                    "status": project.status.value,
                    "total_chunks": project.total_chunks,
                    "is_vectorized": project.is_vectorized,
                    "framework": project.framework,
                },
            )
        except Exception as e:
            logger.error(f"Synchronous ingestion failed for project {project_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@router.get(
    "/projects/{project_id}/status",
    response_model=APIResponse,
    summary="Get ingestion status",
    description="Poll the current ingestion status and chunk count for a project.",
)
def get_ingestion_status(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns current ingestion status:
    - **PENDING** / **PROCESSING** / **COMPLETED**: upload done, ingestion not started
    - **INGESTING**: vectorization in progress
    - **READY_FOR_REVIEW**: ingestion complete, project ready for AI review
    - **FAILED**: ingestion encountered an error (see ingestion_error field)
    """
    user_id = str(current_user.id)
    status_data = IngestionService.get_ingestion_status(db, project_id, user_id)
    return APIResponse(
        success=True,
        message="Ingestion status retrieved.",
        data=status_data,
    )


@router.get(
    "/projects/{project_id}/files-summary",
    response_model=APIResponse,
    summary="Get project file breakdown",
    description=(
        "Returns a detailed file-level breakdown including language distribution, "
        "file list, LOC, and ingestion coverage statistics."
    ),
)
def get_files_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detailed file and language breakdown for a project after ingestion."""
    user_id = str(current_user.id)
    summary = IngestionService.get_project_files_summary(db, project_id, user_id)
    return APIResponse(
        success=True,
        message="Project files summary retrieved.",
        data=summary,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_ingestion_background(project_id: str, user_id: str):
    """
    Background task wrapper for ingestion.
    Creates its own DB session since FastAPI background tasks run outside request scope.
    """
    from backend.app.database.session import SessionLocal
    db = SessionLocal()
    try:
        IngestionService.ingest_project(db, project_id, user_id)
        logger.info(f"Background ingestion complete for project {project_id}")
    except Exception as e:
        logger.error(f"Background ingestion error for project {project_id}: {e}")
    finally:
        db.close()
