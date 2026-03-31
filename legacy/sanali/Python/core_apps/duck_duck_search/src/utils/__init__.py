"""
Utility modules for the DuckDuckGo Image Search application.
"""

from .logging_config import (
    setup_logging,
    get_logger,
    log_operation_start,
    log_operation_complete,
    log_operation_error,
    OperationTimer,
    create_progress_logger
)
from .path_utils import (
    ensure_directory,
    get_cache_path,
    sanitize_filename,
    get_file_hash,
    get_thumbnail_path
)

__all__ = [
    "setup_logging",
    "get_logger",
    "log_operation_start",
    "log_operation_complete",
    "log_operation_error",
    "OperationTimer",
    "create_progress_logger",
    "ensure_directory",
    "get_cache_path",
    "sanitize_filename",
    "get_file_hash",
    "get_thumbnail_path"
]
