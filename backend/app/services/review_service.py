"""
review_service.py — Phase 5 & Phase 6 Service Integration
Service layer bridging the LangGraph multi-agent pipeline and ScoringEngine with PostgreSQL Review records.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.models.file import File
from backend.app.models.review import Review
from backend.app.agents.graph import review_pipeline_graph
from backend.app.agents.state import AgentState
from backend.app.services.scoring_service import ScoringEngine
from backend.app.core.exceptions import NotFoundException, BadRequestException

logger = logging.getLogger(__name__)


class ReviewService:

    @staticmethod
    def run_project_review(db: Session, project_id: str) -> Review:
        """
        Execute the multi-agent code review pipeline for a project and persist findings to DB.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found.")

        # Update project status to analyzing
        project.status = "analyzing"
        db.commit()
        db.refresh(project)

        try:
            # Load project files
            files_db = db.query(File).filter(File.project_id == project_id).all()
            files_context = [
                {
                    "file_id": f.id,
                    "file_path": f.file_path,
                    "filename": f.filename,
                    "language": f.language,
                    "line_count": f.line_count,
                    "content": f.content or "",
                }
                for f in files_db
            ]

            # Construct initial state
            initial_state: AgentState = {
                "project_id": project.id,
                "project_title": project.title,
                "framework": getattr(project, "framework", "Generic") or "Generic",
                "total_files": project.total_files or len(files_context),
                "total_lines_of_code": project.total_lines_of_code or sum(f.line_count for f in files_db),
                "detected_languages": project.detected_languages or [],
                "files_context": files_context,
                "chunks_context": [],
                "code_review_findings": [],
                "bug_findings": [],
                "code_smell_findings": [],
                "security_findings": [],
                "documentation_output": {},
                "test_cases": [],
                "errors": [],
            }

            # Execute LangGraph pipeline
            final_state = review_pipeline_graph.invoke(initial_state)

            findings_payload = {
                "code_review": final_state.get("code_review_findings", []),
                "bugs": final_state.get("bug_findings", []),
                "code_smells": final_state.get("code_smell_findings", []),
                "security": final_state.get("security_findings", []),
            }

            # Recalculate and validate scores using Phase 6 ScoringEngine
            score_breakdown = ScoringEngine.calculate_scores(
                code_review_findings=findings_payload["code_review"],
                bug_findings=findings_payload["bugs"],
                code_smell_findings=findings_payload["code_smells"],
                security_findings=findings_payload["security"],
            )

            # Create or update Review record
            existing_review = db.query(Review).filter(Review.project_id == project_id).order_by(Review.created_at.desc()).first()
            if existing_review:
                review = existing_review
            else:
                review = Review(project_id=project_id)
                db.add(review)

            review.overall_score = score_breakdown.overall_score
            review.grade = score_breakdown.grade
            review.summary = str(final_state.get("summary", ""))

            review.maintainability_score = score_breakdown.maintainability_score
            review.security_score = score_breakdown.security_score
            review.performance_score = score_breakdown.performance_score
            review.readability_score = score_breakdown.readability_score

            review.findings_json = findings_payload
            review.documentation_json = final_state.get("documentation_output", {})
            review.tests_json = final_state.get("test_cases", [])

            # Update project status
            project.status = "completed"

            db.commit()
            db.refresh(review)
            db.refresh(project)

            logger.info(f"Successfully completed multi-agent review for project '{project_id}'. Grade: {review.grade} ({score_breakdown.quality_threshold})")
            return review

        except Exception as e:
            logger.error(f"Failed to run review for project '{project_id}': {e}")
            project.status = "failed"
            db.commit()
            raise BadRequestException(f"Multi-agent review pipeline failed: {str(e)}")

    @staticmethod
    def get_latest_review(db: Session, project_id: str) -> Optional[Review]:
        """Fetch the most recent review record for a project."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found.")

        return db.query(Review).filter(Review.project_id == project_id).order_by(Review.created_at.desc()).first()

    @staticmethod
    def get_review_by_id_or_project(db: Session, identifier: str) -> Optional[Review]:
        """
        Fetch review record by review ID or by project ID (latest review).
        """
        # Try direct review ID lookup
        review = db.query(Review).filter(Review.id == identifier).first()
        if review:
            return review

        # Try project ID lookup (latest review for that project)
        review = db.query(Review).filter(Review.project_id == identifier).order_by(Review.created_at.desc()).first()
        return review
