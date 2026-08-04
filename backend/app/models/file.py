import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database.session import Base
from backend.app.models.base import TimestampMixin


class File(Base, TimestampMixin):
    """File ORM model representing individual source files inside a project."""
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=False, default="unknown")
    file_size_bytes = Column(Integer, default=0, nullable=False)
    line_count = Column(Integer, default=0, nullable=False)
    content_hash = Column(String, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="files")

    __table_args__ = (
        Index("idx_project_filename", "project_id", "filename"),
    )
