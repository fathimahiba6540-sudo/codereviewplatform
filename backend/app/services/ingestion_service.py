"""
ingestion_service.py — Phase 4.3
Orchestration service for the full data ingestion pipeline.

Pipeline:
  1. Load project and resolve extracted repository directory
  2. Parse repository → file metadata (Phase 3 output)
  3. Chunk all ingestible source files (Phase 4.2)
  4. Embed chunks and upsert into ChromaDB (Phase 4.2)
  5. Update project status and metadata in PostgreSQL

Status transitions:
  COMPLETED (from upload/import) → INGESTING → READY_FOR_REVIEW
  Any failure           → FAILED  (with ingestion_error message)
"""
import os
import logging
import asyncio
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundException, AppException
from backend.app.models.project import Project, ProjectStatus
from backend.app.models.file import File
from backend.app.services.repo_parser import RepoParser
from backend.app.services.chunker import CodeChunker
from backend.app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

# Maximum number of files allowed for ingestion in a single run
MAX_INGESTIBLE_FILES = 500

# Maximum total chunks allowed (safety limit to avoid runaway embedding costs)
MAX_TOTAL_CHUNKS = 10_000


class IngestionService:
    """
    Orchestrates the complete Phase 4 ingestion pipeline for a project.
    """

    @classmethod
    def _resolve_project_dir(cls, project_id: str) -> Optional[str]:
        """
        Find the extracted repository directory for a project.
        Convention: UPLOAD_DIR / project_id / <single_subdir>
        """
        project_storage = os.path.join(settings.UPLOAD_DIR, project_id)
        if not os.path.isdir(project_storage):
            return None

        # The extracted repo may be directly at project_storage
        # or one level deeper (e.g., after ZIP extraction)
        subdirs = [
            d for d in os.listdir(project_storage)
            if os.path.isdir(os.path.join(project_storage, d))
        ]
        if subdirs:
            # Pick first subdirectory (the extracted repo root)
            return os.path.join(project_storage, subdirs[0])

        # No subdirs — treat project_storage itself as the repo root
        return project_storage

    @classmethod
    def ingest_project(cls, db: Session, project_id: str, user_id: str) -> Project:
        """
        Run the full ingestion pipeline synchronously.

        Steps:
          1. Validate project ownership and status
          2. Locate extracted repository directory
          3. Parse file structure (or reuse existing DB file records)
          4. Chunk + vectorize all ingestible files
          5. Persist results to PostgreSQL and return updated project

        Raises:
            NotFoundException: if project does not exist or user is not owner.
            AppException: on pipeline failures.
        """
        # 1. Load and validate project
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
        ).first()
        if not project:
            raise NotFoundException(message="Project not found")

        # Guard: don't re-ingest if already fully vectorized
        if project.status == ProjectStatus.READY_FOR_REVIEW and project.is_vectorized:
            logger.info(f"Project {project_id} is already vectorized. Skipping.")
            return project

        # 2. Transition to INGESTING
        project.status = ProjectStatus.INGESTING
        project.ingestion_error = None
        db.commit()

        try:
            # 3. Locate repository directory
            repo_dir = cls._resolve_project_dir(project_id)
            if not repo_dir or not os.path.isdir(repo_dir):
                raise AppException(
                    message=f"Repository files not found for project {project_id}. "
                            "Please re-upload the project."
                )

            logger.info(f"Starting ingestion for project {project_id} at {repo_dir}")

            # 4. Parse repository (refresh metadata)
            parsed_data = RepoParser.parse_repository(repo_dir)

            # Update project metadata fields
            project.total_files = parsed_data["total_files"]
            project.total_lines_of_code = parsed_data["total_lines_of_code"]
            project.detected_languages = parsed_data["detected_languages"]
            project.framework = parsed_data["framework"]
            db.commit()

            # Load file DB records to attach file_id to chunks
            db_files = db.query(File).filter(File.project_id == project_id).all()
            file_id_map = {f.file_path: f.id for f in db_files}

            # Attach DB file IDs to parsed file list
            ingestible_files = []
            for f in parsed_data["files"]:
                if f.get("is_ingestible"):
                    f["db_file_id"] = file_id_map.get(f["file_path"])
                    ingestible_files.append(f)

            if len(ingestible_files) > MAX_INGESTIBLE_FILES:
                logger.warning(
                    f"Project {project_id} has {len(ingestible_files)} ingestible files. "
                    f"Capping at {MAX_INGESTIBLE_FILES}."
                )
                ingestible_files = ingestible_files[:MAX_INGESTIBLE_FILES]

            if not ingestible_files:
                logger.warning(f"Project {project_id} has no ingestible source files.")
                project.status = ProjectStatus.READY_FOR_REVIEW
                project.total_chunks = 0
                project.is_vectorized = True
                db.commit()
                db.refresh(project)
                return project

            # 5. Chunk all ingestible files
            logger.info(f"Chunking {len(ingestible_files)} files for project {project_id}")
            all_chunks = CodeChunker.chunk_project_files(
                files=ingestible_files,
                project_id=project_id,
                repo_dir=repo_dir,
            )

            if len(all_chunks) > MAX_TOTAL_CHUNKS:
                logger.warning(
                    f"Project {project_id} generated {len(all_chunks)} chunks. "
                    f"Capping at {MAX_TOTAL_CHUNKS}."
                )
                all_chunks = all_chunks[:MAX_TOTAL_CHUNKS]

            # 6. Clear existing vectors for idempotency, then upsert fresh chunks
            vector_store.delete_project_collection(project_id)
            total_upserted = vector_store.upsert_chunks(project_id, all_chunks)

            logger.info(
                f"Ingestion complete for project {project_id}: "
                f"{total_upserted} chunks vectorized."
            )

            # 7. Finalize project record
            project.total_chunks = total_upserted
            project.is_vectorized = True
            project.status = ProjectStatus.READY_FOR_REVIEW
            project.ingestion_error = None
            db.commit()
            db.refresh(project)
            return project

        except (NotFoundException, AppException):
            raise
        except Exception as e:
            logger.exception(f"Ingestion failed for project {project_id}: {e}")
            project.status = ProjectStatus.FAILED
            project.ingestion_error = str(e)[:500]
            project.is_vectorized = False
            db.commit()
            raise AppException(message=f"Ingestion pipeline failed: {str(e)}")

    @classmethod
    def get_ingestion_status(cls, db: Session, project_id: str, user_id: str) -> dict:
        """
        Return a concise ingestion status summary for the given project.
        """
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
        ).first()
        if not project:
            raise NotFoundException(message="Project not found")

        chunk_count = vector_store.collection_count(project_id) if project.is_vectorized else 0

        return {
            "project_id": project_id,
            "status": project.status.value,
            "is_vectorized": project.is_vectorized,
            "total_files": project.total_files,
            "total_chunks": project.total_chunks or chunk_count,
            "framework": project.framework,
            "detected_languages": project.detected_languages or [],
            "ingestion_error": project.ingestion_error,
        }

    @classmethod
    def get_project_files_summary(cls, db: Session, project_id: str, user_id: str) -> dict:
        """
        Return a detailed file breakdown for a project: language distribution,
        file list with sizes, and ingestion coverage.
        """
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
        ).first()
        if not project:
            raise NotFoundException(message="Project not found")

        files = db.query(File).filter(File.project_id == project_id).all()

        language_dist: dict = {}
        for f in files:
            language_dist[f.language] = language_dist.get(f.language, 0) + 1

        return {
            "project_id": project_id,
            "title": project.title,
            "framework": project.framework,
            "total_files": project.total_files,
            "total_lines_of_code": project.total_lines_of_code,
            "total_chunks": project.total_chunks,
            "is_vectorized": project.is_vectorized,
            "status": project.status.value,
            "language_distribution": language_dist,
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "file_path": f.file_path,
                    "language": f.language,
                    "line_count": f.line_count,
                    "file_size_bytes": f.file_size_bytes,
                }
                for f in sorted(files, key=lambda x: x.file_path)
            ],
        }
