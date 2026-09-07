from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.comment import ReviewComment
from backend.app.models.schemas import APIResponse
from backend.app.routers.deps import get_current_active_user

router = APIRouter(tags=["Collaborative Comments"])


class CommentCreate(BaseModel):
    file_path: Optional[str] = None
    line_number: Optional[str] = None
    comment_text: str = Field(..., min_length=1)


@router.post("/reviews/{review_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(
    review_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a collaborative review comment to a review report or finding."""
    comment = ReviewComment(
        review_id=review_id,
        user_id=current_user.id,
        file_path=payload.file_path,
        line_number=payload.line_number,
        comment_text=payload.comment_text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return APIResponse(
        success=True,
        message="Review comment created successfully",
        data={
            "id": comment.id,
            "review_id": comment.review_id,
            "user_id": comment.user_id,
            "author": current_user.username,
            "file_path": comment.file_path,
            "line_number": comment.line_number,
            "comment_text": comment.comment_text,
            "created_at": comment.created_at.isoformat(),
        }
    )


@router.get("/reviews/{review_id}/comments", status_code=status.HTTP_200_OK)
def list_comments(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all comments posted on a review report."""
    comments = db.query(ReviewComment).filter(ReviewComment.review_id == review_id).order_by(ReviewComment.created_at.asc()).all()

    return APIResponse(
        success=True,
        message=f"Retrieved {len(comments)} comment(s)",
        data=[
            {
                "id": c.id,
                "review_id": c.review_id,
                "user_id": c.user_id,
                "file_path": c.file_path,
                "line_number": c.line_number,
                "comment_text": c.comment_text,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]
    )
