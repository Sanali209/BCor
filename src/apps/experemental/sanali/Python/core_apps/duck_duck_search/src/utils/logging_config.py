"""
Logging configuration for DuckDuckGo Image Search application.
Uses loguru for comprehensive logging with structured output.
"""

import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    max_file_size: str = "10 MB",
    retention_period: str = "30 days"
) -> None:
    """
    Set up comprehensive logging configuration.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Custom log file path (auto-generated if None)
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
        max_file_size: Maximum size per log file before rotation
        retention_period: How long to keep log files
    """
    # Remove any existing handlers
    logger.remove()

    # Configure console logging
    if enable_console:
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

    # Configure file logging
    if enable_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Generate log file path if not provided
        if log_file is None:
            log_file = f"logs/duck_duck_search_{Path.cwd().name}.log"

        logger.add(
            log_file,
            rotation=max_file_size,
            retention=retention_period,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level="DEBUG",  # Always log debug to file
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )

    # Add specific logger for performance monitoring
    performance_logger = logger.bind(logger_type="performance")
    logger.add(
        "logs/performance.log",
        filter=lambda record: record["extra"].get("logger_type") == "performance",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        rotation="50 MB",
        retention="7 days"
    )


def get_logger(name: str) -> logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logger.bind(module=name)


def log_operation_start(operation_name: str, **context) -> str:
    """
    Log the start of an operation with context.

    Args:
        operation_name: Name of the operation
        **context: Additional context data

    Returns:
        Operation ID for tracking
    """
    import uuid
    operation_id = str(uuid.uuid4())[:8]

    context_data = {"operation_id": operation_id, "phase": "start", **context}
    logger.info(f"Starting operation: {operation_name}", **context_data)

    return operation_id


def log_operation_complete(operation_id: str, operation_name: str, duration: float, **context) -> None:
    """
    Log the completion of an operation.

    Args:
        operation_id: Operation ID from log_operation_start
        operation_name: Name of the operation
        duration: Operation duration in seconds
        **context: Additional context data
    """
    context_data = {
        "operation_id": operation_id,
        "phase": "complete",
        "duration": f"{duration:.3f}s",
        **context
    }
    logger.info(f"Completed operation: {operation_name}", **context_data)


def log_operation_error(operation_id: str, operation_name: str, error: Exception, **context) -> None:
    """
    Log an operation error.

    Args:
        operation_id: Operation ID from log_operation_start
        operation_name: Name of the operation
        error: The exception that occurred
        **context: Additional context data
    """
    context_data = {
        "operation_id": operation_id,
        "phase": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context
    }
    logger.error(f"Failed operation: {operation_name}", **context_data)


class OperationTimer:
    """
    Context manager for timing operations with automatic logging.
    """

    def __init__(self, operation_name: str, logger_instance=None, **context):
        self.operation_name = operation_name
        self.logger_instance = logger_instance or logger
        self.context = context
        self.start_time = None
        self.operation_id = None

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else time.time()
        self.operation_id = log_operation_start(self.operation_name, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else time.time()
        duration = end_time - self.start_time

        if exc_type is not None:
            log_operation_error(self.operation_id, self.operation_name, exc_val, **self.context)
        else:
            log_operation_complete(self.operation_id, self.operation_name, duration, **self.context)


# Import here to avoid circular imports
import asyncio
import time


def create_progress_logger(operation_name: str):
    """
    Create a logger specifically for progress updates.

    Args:
        operation_name: Name of the operation for progress tracking

    Returns:
        Logger function for progress updates
    """
    def progress_logger(current: int, total: int, message: str = None):
        percentage = (current / total * 100) if total > 0 else 0
        progress_msg = (
            f"Progress: {current}/{total} ({percentage:.1f}%) - {message}"
            if message else f"Progress: {current}/{total} ({percentage:.1f}%)"
        )

        logger.info(progress_msg, operation=operation_name, current=current, total=total, percentage=percentage)

    return progress_logger
