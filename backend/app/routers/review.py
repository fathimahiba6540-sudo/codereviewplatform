"""
review.py — Phase 5 API Integration
Endpoints to trigger multi-agent code reviews and retrieve review reports.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.schemas import APIResponse
from backend.app.routers.deps import get_current_active_user
from backend.app.services.review_service import ReviewService
from backend.app.core.exceptions import NotFoundException

router = APIRouter(tags=["Code Reviews"])


@router.post("/projects/{project_id}/review", status_code=status.HTTP_200_OK)
def trigger_code_review(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Trigger the multi-agent AI code review pipeline for a project.
    Runs 7 specialized AI agents (Code Review, Bug Finder, Code Smell, Security, Documentation, Test Generator, Summary).
    """
    review = ReviewService.run_project_review(db=db, project_id=project_id)
    return APIResponse(
        success=True,
        message=f"Code review pipeline completed successfully. Overall Grade: {review.grade}",
        data={
            "id": review.id,
            "project_id": review.project_id,
            "overall_score": review.overall_score,
            "grade": review.grade,
            "summary": review.summary,
            "component_scores": {
                "maintainability": review.maintainability_score,
                "security": review.security_score,
                "performance": review.performance_score,
                "readability": review.readability_score,
            },
            "findings": review.findings_json,
            "documentation": review.documentation_json,
            "test_cases": review.tests_json,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
    )


@router.get("/projects/{project_id}/review", status_code=status.HTTP_200_OK)
@router.get("/review/{id}", status_code=status.HTTP_200_OK)
def get_project_review(
    project_id: str = None,
    id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve code review report by project ID or review ID."""
    target_id = id or project_id
    review = ReviewService.get_review_by_id_or_project(db=db, identifier=target_id)
    if not review:
        raise NotFoundException(f"No review report found for ID/Project '{target_id}'. Please run a review first.")

    return APIResponse(
        success=True,
        message="Review report retrieved successfully",
        data={
            "id": review.id,
            "project_id": review.project_id,
            "overall_score": review.overall_score,
            "grade": review.grade,
            "summary": review.summary,
            "component_scores": {
                "maintainability": review.maintainability_score,
                "security": review.security_score,
                "performance": review.performance_score,
                "readability": review.readability_score,
            },
            "findings": review.findings_json,
            "documentation": review.documentation_json,
            "test_cases": review.tests_json,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
    )


@router.get("/projects/{project_id}/documentation", status_code=status.HTTP_200_OK)
@router.get("/documentation/{id}", status_code=status.HTTP_200_OK)
def get_documentation(
    project_id: str = None,
    id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve generated project documentation report."""
    target_id = id or project_id
    review = ReviewService.get_review_by_id_or_project(db=db, identifier=target_id)
    if not review:
        raise NotFoundException(f"No documentation found for ID/Project '{target_id}'.")

    return APIResponse(
        success=True,
        message="Documentation report retrieved successfully",
        data=review.documentation_json or {}
    )


@router.get("/projects/{project_id}/security", status_code=status.HTTP_200_OK)
@router.get("/security/{id}", status_code=status.HTTP_200_OK)
def get_security_findings(
    project_id: str = None,
    id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve security vulnerability findings and security score."""
    target_id = id or project_id
    review = ReviewService.get_review_by_id_or_project(db=db, identifier=target_id)
    if not review:
        raise NotFoundException(f"No security report found for ID/Project '{target_id}'.")

    findings = review.findings_json or {}
    security_findings = findings.get("security", [])

    return APIResponse(
        success=True,
        message="Security findings retrieved successfully",
        data={
            "project_id": review.project_id,
            "security_score": review.security_score,
            "total_vulnerabilities": len(security_findings),
            "vulnerabilities": security_findings
        }
    )


@router.get("/projects/{project_id}/tests", status_code=status.HTTP_200_OK)
@router.get("/tests/{id}", status_code=status.HTTP_200_OK)
def get_generated_tests(
    project_id: str = None,
    id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve AI generated test cases."""
    target_id = id or project_id
    review = ReviewService.get_review_by_id_or_project(db=db, identifier=target_id)
    if not review:
        raise NotFoundException(f"No generated tests found for ID/Project '{target_id}'.")

    return APIResponse(
        success=True,
        message="Generated tests retrieved successfully",
        data={
            "project_id": review.project_id,
            "total_test_cases": len(review.tests_json or []),
            "test_cases": review.tests_json or []
        }
    )


@router.get("/review/{base_review_id}/compare/{target_review_id}", status_code=status.HTTP_200_OK)
def compare_reviews(
    base_review_id: str,
    target_review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Compare two code review reports and calculate score deltas and findings diff."""
    from backend.app.services.comparison_service import ComparisonService

    base_review = ReviewService.get_review_by_id_or_project(db=db, identifier=base_review_id)
    target_review = ReviewService.get_review_by_id_or_project(db=db, identifier=target_review_id)

    if not base_review or not target_review:
        raise NotFoundException("One or both review reports requested for comparison were not found.")

    diff_data = ComparisonService.compare_reviews(base_review, target_review)
    return APIResponse(
        success=True,
        message="Review comparison generated successfully",
        data=diff_data
    )


@router.get("/projects/{project_id}/history", status_code=status.HTTP_200_OK)
def get_project_review_history(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve history of all review runs for a project."""
    reviews = db.query(ReviewService.get_review_model()).filter_by(project_id=project_id).all() if hasattr(ReviewService, 'get_review_model') else []
    
    # Fallback ORM query
    from backend.app.models.review import Review
    reviews = db.query(Review).filter(Review.project_id == project_id).order_by(Review.created_at.desc()).all()

    history = [
        {
            "id": r.id,
            "overall_score": r.overall_score,
            "grade": r.grade,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(history)} historical review run(s)",
        data={
            "project_id": project_id,
            "total_reviews": len(history),
            "history": history
        }
    )


