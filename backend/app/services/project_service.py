import os
import shutil
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundException, AppException
from backend.app.models.project import Project, SourceType, ProjectStatus
from backend.app.models.file import File
from backend.app.models.review import Review
from backend.app.services.repo_parser import RepoParser


class ProjectService:
    """Service orchestrating Project database entities and file storage lifecycle."""

    @classmethod
    def create_project(
        cls,
        db: Session,
        user_id: str,
        title: str,
        source_type: SourceType,
        github_url: Optional[str] = None
    ) -> Project:
        """Create initial Project record with PENDING status."""
        project = Project(
            user_id=user_id,
            title=title,
            source_type=source_type,
            github_url=github_url,
            status=ProjectStatus.PENDING
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @classmethod
    def process_and_save_repository(
        cls,
        db: Session,
        project_id: str,
        extracted_dir: str
    ) -> Project:
        """Parse extracted directory and persist file metadata records to PostgreSQL."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundException(message="Project not found")

        try:
            project.status = ProjectStatus.PROCESSING
            db.commit()

            # Parse repository structure
            parsed_data = RepoParser.parse_repository(extracted_dir)

            # Update project metadata
            project.total_files = parsed_data["total_files"]
            project.total_lines_of_code = parsed_data["total_lines_of_code"]
            project.detected_languages = parsed_data["detected_languages"]
            project.status = ProjectStatus.COMPLETED

            # Delete existing files for project if re-parsing
            db.query(File).filter(File.project_id == project_id).delete()

            # Insert file records
            for file_info in parsed_data["files"]:
                db_file = File(
                    project_id=project_id,
                    filename=file_info["filename"],
                    file_path=file_info["file_path"],
                    language=file_info["language"],
                    file_size_bytes=file_info["file_size_bytes"],
                    line_count=file_info["line_count"],
                    content_hash=file_info["content_hash"]
                )
                db.add(db_file)

            db.commit()
            db.refresh(project)
            return project

        except Exception as e:
            project.status = ProjectStatus.FAILED
            db.commit()
            raise AppException(message=f"Failed to parse repository structure: {str(e)}")

    @classmethod
    def get_user_projects(cls, db: Session, user_id: str) -> List[Project]:
        """Fetch all projects owned by a user ordered by newest first."""
        return db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()

    @classmethod
    def get_project_by_id(cls, db: Session, project_id: str, user_id: str) -> Project:
        """Fetch project by ID, ensuring user ownership."""
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
        if not project:
            raise NotFoundException(message="Project not found")
        return project

    @classmethod
    def get_project_files(cls, db: Session, project_id: str, user_id: str) -> List[File]:
        """Fetch all parsed file records for a project."""
        cls.get_project_by_id(db, project_id, user_id)
        return db.query(File).filter(File.project_id == project_id).order_by(File.file_path.asc()).all()

    @classmethod
    def delete_project(cls, db: Session, project_id: str, user_id: str) -> bool:
        """Delete project record from database and purge extracted storage files."""
        project = cls.get_project_by_id(db, project_id, user_id)

        # Remove local storage directory
        project_storage_dir = os.path.join(settings.UPLOAD_DIR, project_id)
        if os.path.exists(project_storage_dir):
            shutil.rmtree(project_storage_dir, ignore_errors=True)

        db.delete(project)
        db.commit()
        return True
