"""Logging configuration utilities.

Provides consistent logging setup across all scripts and modules.

TODO (Framework Evolution):
    - Structured logging (JSON format) for machine parsing
    - Log aggregation (send to centralized logging service)
    - Different log levels per module
    - Performance profiling integration
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "logs/football_analytics.log",
    console_output: bool = True,
    format_string: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.

    Sets up both file and console logging with consistent formatting.
    Creates log directory if it doesn't exist.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only console logging is used.
        console_output: Whether to also print logs to console (default: True)
        format_string: Custom format string. If None, uses default format.

    Example:
        >>> setup_logging(level="DEBUG", log_file="logs/debug.log")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Logging configured")

    TODO (Framework Evolution):
        - Add rotation (RotatingFileHandler for size-based rotation)
        - Add TimedRotatingFileHandler for daily logs
        - Add filters for sensitive data (API keys, etc.)
        - Add colored console output for better readability
    """
    # Default format with timestamp, logger name, level, and message
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create handlers list
    handlers = []

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(console_handler)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level, handlers=handlers, force=True  # Override any existing configuration
    )

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured: level={level}, file={log_file}")


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional custom level.

    Args:
        name: Logger name (typically __name__)
        level: Optional logging level override

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
    """
    logger = logging.getLogger(name)

    if level:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

    return logger


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.

    Useful for debugging and tracking execution flow.

    Example:
        >>> @log_function_call
        ... def process_data(data):
        ...     return len(data)
        >>> process_data([1, 2, 3])
        # Logs: "Calling process_data with args=([1, 2, 3],), kwargs={}"
        # Logs: "process_data returned 3"

    TODO (Framework Evolution):
        - Add execution time logging
        - Add exception logging
        - Make it configurable (enable/disable per environment)
    """

    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logger.debug(f"{func.__name__} returned {result}")
        return result

    return wrapper
