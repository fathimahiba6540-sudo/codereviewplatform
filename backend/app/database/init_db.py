from backend.app.database.session import engine, Base
from backend.app.models import User, Project, File, Review
from backend.app.core.logging import logger


def init_db():
    """Create all database tables using SQLAlchemy engine if they do not exist."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
