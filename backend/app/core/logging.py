import logging
import sys


def setup_logging():
    """Configure structured logging for stdout."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Standard stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(handler)
    return logger


logger = setup_logging()
