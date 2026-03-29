"""
Image Processor Logger - Comprehensive logging for image processing pipelines
Provides structured logging with image context, processing phases, and performance metrics
"""
import os
import time
import json
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import contextmanager

from loguru import logger


class ProcessingPhase(Enum):
    """Image processing pipeline phases"""
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    PREPROCESSING = "preprocessing"
    INFERENCE = "inference"
    POST_PROCESSING = "post_processing"
    STORAGE = "storage"
    CLEANUP = "cleanup"


class LogLevel(Enum):
    """Log levels for different types of events"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ImageContext:
    """Context information for an image being processed"""
    image_path: str
    image_size: Optional[int] = None
    image_format: Optional[str] = None
    batch_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def filename(self) -> str:
        return Path(self.image_path).name

    @property
    def directory(self) -> str:
        return str(Path(self.image_path).parent)


@dataclass
class ProcessingEvent:
    """Structured log event for image processing"""
    timestamp: str
    phase: ProcessingPhase
    level: LogLevel
    image_context: ImageContext
    operation: str
    message: str
    duration_ms: Optional[float] = None
    error_details: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    stack_info: Optional[str] = None

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['phase'] = self.phase.value
        data['level'] = self.level.value
        data['image_context'] = asdict(self.image_context)
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ImageProcessorLogger:
    """
    Centralized logger for image processing operations
    Tracks processing phases, performance, and bottlenecks
    """

    def __init__(self, log_directory: str = "logs/image_processing"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Thread-safe storage for current processing state
        self._current_operations = {}
        self._lock = threading.RLock()

        # Session tracking
        self.session_id = f"session_{int(time.time())}"
        self.session_start = datetime.now()

        # Setup loguru logger
        self._setup_logger()

        # Performance tracking
        self.phase_timings = {}
        self.error_counts = {}

    def _setup_logger(self):
        """Setup loguru logger with structured output"""
        # Remove default handler
        logger.remove()

        # Add console handler for real-time monitoring
        logger.add(
            lambda msg: print(msg, end=""),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[phase]:<15} | {extra[operation]:<20} | {extra[image]} | {message}",
            level="INFO",
            enqueue=True
        )

        # Add file handler for detailed structured logs
        log_file = self.log_directory / f"image_processing_{self.session_id}.log"
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[phase]:<15} | {extra[operation]:<20} | {extra[image]} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            enqueue=True,
            serialize=True
        )

        # Add JSON structured log file
        json_log_file = self.log_directory / f"image_processing_{self.session_id}.jsonl"
        logger.add(
            json_log_file,
            format="{message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            enqueue=True,
            serialize=False  # We'll handle JSON serialization ourselves
        )

    @contextmanager
    def operation_context(self, phase: ProcessingPhase, operation: str, image_context: ImageContext):
        """
        Context manager for tracking operation duration and handling errors
        """
        start_time = time.time()
        operation_id = f"{threading.current_thread().ident}_{id(image_context)}"

        with self._lock:
            self._current_operations[operation_id] = {
                'phase': phase,
                'operation': operation,
                'image_context': image_context,
                'start_time': start_time
            }

        try:
            # Log operation start
            self.log_event(
                phase=phase,
                level=LogLevel.DEBUG,
                image_context=image_context,
                operation=f"{operation}_start",
                message=f"Started {operation} for {image_context.filename}"
            )

            yield

            # Log successful completion
            duration = (time.time() - start_time) * 1000
            self.log_event(
                phase=phase,
                level=LogLevel.DEBUG,
                image_context=image_context,
                operation=f"{operation}_complete",
                message=f"Completed {operation} for {image_context.filename}",
                duration_ms=duration
            )

        except Exception as e:
            # Log failure with error details
            duration = (time.time() - start_time) * 1000
            self.log_event(
                phase=phase,
                level=LogLevel.ERROR,
                image_context=image_context,
                operation=f"{operation}_failed",
                message=f"Failed {operation} for {image_context.filename}: {str(e)}",
                duration_ms=duration,
                error_details=str(e),
                stack_info=self._get_stack_info()
            )
            raise
        finally:
            with self._lock:
                self._current_operations.pop(operation_id, None)

    def log_event(
        self,
        phase: ProcessingPhase,
        level: LogLevel,
        image_context: ImageContext,
        operation: str,
        message: str,
        duration_ms: Optional[float] = None,
        error_details: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        stack_info: Optional[str] = None
    ):
        """
        Log a processing event with full context
        """
        event = ProcessingEvent(
            timestamp=datetime.now().isoformat(),
            phase=phase,
            level=level,
            image_context=image_context,
            operation=operation,
            message=message,
            duration_ms=duration_ms,
            error_details=error_details,
            performance_metrics=performance_metrics or {},
            stack_info=stack_info
        )

        # Update performance tracking
        if duration_ms is not None:
            phase_key = f"{phase.value}_{operation}"
            if phase_key not in self.phase_timings:
                self.phase_timings[phase_key] = []
            self.phase_timings[phase_key].append(duration_ms)

        # Update error tracking
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            error_key = f"{phase.value}_{operation}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Log with structured context
        extra = {
            'phase': phase.value,
            'operation': operation,
            'image': image_context.filename,
            'image_path': image_context.image_path,
            'batch_id': image_context.batch_id,
            'session_id': image_context.session_id or self.session_id
        }

        # Choose loguru method based on level
        log_method = {
            LogLevel.DEBUG: logger.debug,
            LogLevel.INFO: logger.info,
            LogLevel.WARNING: logger.warning,
            LogLevel.ERROR: logger.error,
            LogLevel.CRITICAL: logger.critical
        }[level]

        # Use bind() to avoid conflicts with loguru's internal 'extra' field
        bound_logger = logger.bind(**extra)
        log_method = getattr(bound_logger, level.value.lower())
        log_method(message)

        # Also write structured JSON to file
        self._write_structured_log(event)

    def _write_structured_log(self, event: ProcessingEvent):
        """Write structured event to JSON log file"""
        json_log_file = self.log_directory / f"image_processing_{self.session_id}.jsonl"
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + '\n')
        except Exception as e:
            logger.error(f"Failed to write structured log: {e}")

    def _get_stack_info(self) -> str:
        """Get current stack information for debugging"""
        import traceback
        return ''.join(traceback.format_stack()[-3:-1])  # Get last 2 stack frames

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for the session"""
        report = {
            'session_id': self.session_id,
            'session_duration': (datetime.now() - self.session_start).total_seconds(),
            'phase_timings': {},
            'error_counts': self.error_counts.copy(),
            'total_operations': len(self._current_operations)
        }

        # Calculate phase timing statistics
        for phase_op, timings in self.phase_timings.items():
            if timings:
                report['phase_timings'][phase_op] = {
                    'count': len(timings),
                    'avg_ms': sum(timings) / len(timings),
                    'min_ms': min(timings),
                    'max_ms': max(timings),
                    'total_ms': sum(timings)
                }

        return report

    def get_stuck_images_report(self, timeout_seconds: int = 300) -> List[Dict[str, Any]]:
        """Identify images that appear to be stuck in processing"""
        stuck_images = []
        current_time = time.time()

        with self._lock:
            for op_id, op_data in self._current_operations.items():
                elapsed = current_time - op_data['start_time']
                if elapsed > timeout_seconds:
                    stuck_images.append({
                        'operation_id': op_id,
                        'phase': op_data['phase'].value,
                        'operation': op_data['operation'],
                        'image_path': op_data['image_context'].image_path,
                        'elapsed_seconds': elapsed,
                        'start_time': datetime.fromtimestamp(op_data['start_time']).isoformat()
                    })

        return stuck_images

    def log_batch_progress(self, batch_id: str, completed: int, total: int, stuck_images: List[str] = None):
        """Log batch processing progress with stuck image detection"""
        progress_pct = (completed / total * 100) if total > 0 else 0

        message = f"Batch {batch_id}: {completed}/{total} images processed ({progress_pct:.1f}%)"

        if stuck_images:
            message += f" | STUCK IMAGES: {len(stuck_images)} - {', '.join(stuck_images[:5])}"
            if len(stuck_images) > 5:
                message += f" ... and {len(stuck_images) - 5} more"

        # Create dummy image context for batch logging
        batch_context = ImageContext(
            image_path=f"batch:{batch_id}",
            batch_id=batch_id,
            session_id=self.session_id
        )

        self.log_event(
            phase=ProcessingPhase.CLEANUP,
            level=LogLevel.INFO,
            image_context=batch_context,
            operation="batch_progress",
            message=message,
            performance_metrics={
                'completed': completed,
                'total': total,
                'progress_pct': progress_pct,
                'stuck_count': len(stuck_images) if stuck_images else 0
            }
        )


# Global logger instance
image_logger = ImageProcessorLogger()


def get_image_context(image_path: str, batch_id: Optional[str] = None, **metadata) -> ImageContext:
    """
    Create an ImageContext with automatic metadata extraction
    """
    context = ImageContext(
        image_path=image_path,
        batch_id=batch_id,
        session_id=image_logger.session_id,
        metadata=metadata
    )

    # Try to get file size and format
    try:
        path = Path(image_path)
        if path.exists():
            context.image_size = path.stat().st_size
            context.image_format = path.suffix.lower().lstrip('.')
    except Exception:
        pass  # Ignore errors in metadata extraction

    return context


# Convenience functions for common logging patterns
def log_image_discovery(image_path: str, batch_id: Optional[str] = None, **metadata):
    """Log image discovery phase"""
    context = get_image_context(image_path, batch_id, **metadata)
    image_logger.log_event(
        phase=ProcessingPhase.DISCOVERY,
        level=LogLevel.INFO,
        image_context=context,
        operation="image_discovered",
        message=f"Discovered image: {context.filename}"
    )


def log_image_validation(image_path: str, is_valid: bool, validation_errors: List[str] = None, batch_id: Optional[str] = None):
    """Log image validation phase"""
    context = get_image_context(image_path, batch_id)
    level = LogLevel.INFO if is_valid else LogLevel.WARNING
    message = f"Image validation {'PASSED' if is_valid else 'FAILED'}: {context.filename}"

    if validation_errors:
        message += f" | Errors: {', '.join(validation_errors)}"

    image_logger.log_event(
        phase=ProcessingPhase.VALIDATION,
        level=level,
        image_context=context,
        operation="image_validation",
        message=message,
        performance_metrics={'is_valid': is_valid, 'error_count': len(validation_errors) if validation_errors else 0}
    )


def log_processing_stuck(image_path: str, phase: ProcessingPhase, operation: str, elapsed_seconds: float, batch_id: Optional[str] = None):
    """Log when processing appears stuck on an image"""
    context = get_image_context(image_path, batch_id)
    image_logger.log_event(
        phase=phase,
        level=LogLevel.CRITICAL,
        image_context=context,
        operation=f"{operation}_stuck",
        message=f"PROCESSING STUCK: {context.filename} stuck in {operation} for {elapsed_seconds:.1f}s",
        performance_metrics={'elapsed_seconds': elapsed_seconds, 'stuck': True}
    )
