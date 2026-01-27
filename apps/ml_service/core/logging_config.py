"""
Logging Configuration for ML Service

Provides structured logging with:
- Consistent format across all modules
- Configurable log levels
- Reduced noise from external libraries
"""

import logging
import sys
from typing import Optional


# Default format: timestamp | level | module:function:line | message
DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
)

# Simplified format for production
PRODUCTION_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    production_mode: bool = False,
) -> logging.Logger:
    """
    Configure structured logging for the ML service.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format (optional)
        production_mode: If True, use simplified format

    Returns:
        Configured root logger for ml_service

    Example:
        >>> logger = setup_logging(level=logging.DEBUG)
        >>> logger.info("ML service starting")
    """
    if format_string is None:
        format_string = PRODUCTION_FORMAT if production_mode else DEFAULT_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )

    # Create ml_service logger
    logger = logging.getLogger("ml_service")
    logger.setLevel(level)

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger.info(f"Logging configured: level={logging.getLevelName(level)}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance with ml_service prefix

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Processing telemetry data")
    """
    # Ensure name is prefixed with ml_service
    if not name.startswith("ml_service"):
        name = f"ml_service.{name}"

    return logging.getLogger(name)
