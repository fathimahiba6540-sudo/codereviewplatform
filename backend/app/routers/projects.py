import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Form, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.database.session import get_db
from backend.app.routers.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.project import SourceType
from backend.app.models.schemas import (
    APIResponse,
    ProjectResponse,
    ProjectSummaryResponse,
    FileResponse,
    GitHubImportRequest,
    TitleOnlyProjectRequest
)
from backend.app.services.zip_service import ZipService
from backend.app.services.github_service import GitHubService
from backend.app.services.project_service import ProjectService
from backend.app.services.repo_parser import RepoParser
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/projects", tags=["Projects & Repository Imports"])


@router.post(
    "/create-title",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project using only Project Title & Description"
)
@router.post(
    "/title",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project using only Project Title & Description (alias)"
)
def create_project_from_title_endpoint(
    req: TitleOnlyProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create project from Title only, generate starter codebase, and save metadata."""
    project = ProjectService.create_project_from_title(
        db=db,
        user_id=current_user.id,
        title=req.title,
        description=req.description,
        language=req.language
    )
    return APIResponse(
        message="Project created successfully from title with boilerplate starter codebase",
        data=ProjectResponse.model_validate(project)
    )



@router.post(
    "/upload-zip",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload project source code via ZIP archive"
)
@router.post(
    "/upload",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload project source code via ZIP archive (alias)"
)
async def upload_project_zip(
    file: UploadFile = FastAPIFile(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload ZIP archive, validate, extract, parse codebase, and save metadata."""
    if not file.filename.endswith(".zip"):
        raise AppException(message="Only .zip archive files are accepted", code="INVALID_FILE_TYPE")

    project_title = title if title else os.path.splitext(file.filename)[0]

    # Create initial project record
    project = ProjectService.create_project(
        db=db,
        user_id=current_user.id,
        title=project_title,
        source_type=SourceType.ZIP
    )

    # Save uploaded zip file temporarily
    project_dir = os.path.join(settings.UPLOAD_DIR, project.id)
    zip_path = os.path.join(settings.UPLOAD_DIR, f"{project.id}.zip")

    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(zip_path, "wb") as f:
            content = await file.read()
            if len(content) > ZipService.MAX_SIZE_BYTES:
                raise AppException(message="ZIP file size exceeds maximum limit of 50 MB", code="ZIP_TOO_LARGE")
            f.write(content)

        # Validate header
        if not ZipService.validate_zip_header(zip_path):
            raise AppException(message="Corrupt or invalid ZIP archive header", code="INVALID_ZIP")

        # Extract archive safely
        ZipService.extract_zip(zip_path, project_dir)

        # Process and parse repository
        updated_project = ProjectService.process_and_save_repository(db, project.id, project_dir)

        return APIResponse(
            message="Project ZIP archive uploaded and parsed successfully",
            data=ProjectResponse.model_validate(updated_project)
        )

    finally:
        # Clean up temporary zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)


@router.post(
    "/import-github",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Import repository from public GitHub URL"
)
@router.post(
    "/github",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Import repository from public GitHub URL (alias)"
)
async def import_github_repository(
    import_in: GitHubImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Import repository directly from GitHub URL, download tarball archive, and parse codebase."""
    owner, repo = GitHubService.parse_github_url(import_in.github_url)
    project_title = import_in.title if import_in.title else f"{owner}/{repo}"

    # Verify repository metadata first
    repo_meta = await GitHubService.fetch_repo_metadata(owner, repo, access_token=import_in.github_token)

    # Create project record
    project = ProjectService.create_project(
        db=db,
        user_id=current_user.id,
        title=project_title,
        source_type=SourceType.GITHUB,
        github_url=import_in.github_url
    )

    project_dir = os.path.join(settings.UPLOAD_DIR, project.id)

    # Download and extract archive
    await GitHubService.download_and_extract_repo(owner, repo, project_dir, access_token=import_in.github_token)

    # Process and save repository
    updated_project = ProjectService.process_and_save_repository(db, project.id, project_dir)

    return APIResponse(
        message="GitHub repository imported and parsed successfully",
        data=ProjectResponse.model_validate(updated_project)
    )


@router.get(
    "",
    response_model=APIResponse[List[ProjectResponse]],
    summary="List all user projects"
)
def list_user_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch all imported projects owned by current user."""
    projects = ProjectService.get_user_projects(db, current_user.id)
    return APIResponse(
        data=[ProjectResponse.model_validate(p) for p in projects]
    )


@router.get(
    "/{project_id}",
    response_model=APIResponse[ProjectSummaryResponse],
    summary="Get project details and summary dashboard payload"
)
def get_project_details(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch details and dashboard summary payload for a specific project."""
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    files = ProjectService.get_project_files(db, project_id, current_user.id)

    # Detect framework
    project_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    framework = "Generic Codebase"
    if os.path.exists(project_dir):
        file_paths = [os.path.join(project_dir, f.file_path) for f in files]
        framework = RepoParser.detect_framework(project_dir, file_paths)

    recent_files = [FileResponse.model_validate(f) for f in files[:10]]

    # Get latest review if available
    review = ReviewService.get_review_by_id_or_project(db, project_id)
    latest_review_dict = None
    if review:
        latest_review_dict = {
            "id": review.id,
            "overall_score": review.overall_score,
            "grade": review.grade,
            "summary": review.summary,
            "component_scores": {
                "maintainability": review.maintainability_score,
                "security": review.security_score,
                "performance": review.performance_score,
                "readability": review.readability_score,
            },
            "created_at": review.created_at.isoformat() if review.created_at else None
        }

    summary = ProjectSummaryResponse(
        project=ProjectResponse.model_validate(project),
        framework=framework,
        file_count=project.total_files,
        lines_of_code=project.total_lines_of_code,
        languages=project.detected_languages,
        recent_files=recent_files,
        latest_review=latest_review_dict
    )

    return APIResponse(data=summary)



@router.get(
    "/{project_id}/files",
    response_model=APIResponse[List[FileResponse]],
    summary="List all parsed files for a project"
)
def list_project_files(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch all files associated with a project."""
    files = ProjectService.get_project_files(db, project_id, current_user.id)
    return APIResponse(
        data=[FileResponse.model_validate(f) for f in files]
    )


@router.delete(
    "/{project_id}",
    response_model=APIResponse[dict],
    summary="Delete a project"
)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete project, parsed file records, and storage directory."""
    ProjectService.delete_project(db, project_id, current_user.id)
    return APIResponse(message="Project deleted successfully")
