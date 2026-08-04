import uuid
from sqlalchemy import Column, String, Float, ForeignKey, JSON, Index, Text
from sqlalchemy.orm import relationship
from backend.app.database.session import Base
from backend.app.models.base import TimestampMixin


class Review(Base, TimestampMixin):
    """Review ORM model storing AI analysis reports and scores."""
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    overall_score = Column(Float, nullable=False, default=0.0)
    grade = Column(String, nullable=False, default="F")
    summary = Column(Text, nullable=True)

    # Component Scores
    maintainability_score = Column(Float, nullable=False, default=0.0)
    security_score = Column(Float, nullable=False, default=0.0)
    performance_score = Column(Float, nullable=False, default=0.0)
    readability_score = Column(Float, nullable=False, default=0.0)

    # Detailed Findings JSON payloads
    findings_json = Column(JSON, default=dict, nullable=False)
    documentation_json = Column(JSON, default=dict, nullable=False)
    tests_json = Column(JSON, default=list, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="reviews")

    __table_args__ = (
        Index("idx_project_review_created", "project_id", "created_at"),
    )
