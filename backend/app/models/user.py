import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from backend.app.database.session import Base
from backend.app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """User ORM model representing platform users."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
