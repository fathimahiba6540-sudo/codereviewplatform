import uuid
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
from backend.app.database.session import Base
from backend.app.models.base import TimestampMixin


class SourceType(str, enum.Enum):
    ZIP = "ZIP"
    GITHUB = "GITHUB"


class ProjectStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Project(Base, TimestampMixin):
    """Project ORM model representing imported codebases."""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    github_url = Column(String, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING, nullable=False, index=True)
    
    total_files = Column(Integer, default=0, nullable=False)
    total_lines_of_code = Column(Integer, default=0, nullable=False)
    detected_languages = Column(JSON, default=list, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_project_status", "user_id", "status"),
    )
