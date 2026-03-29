"""
SLM Logging Module
Provides comprehensive logging for image processing and other operations
"""

from .image_processor_logger import (
    ImageProcessorLogger,
    ProcessingPhase,
    LogLevel,
    ImageContext,
    ProcessingEvent,
    image_logger,
    get_image_context,
    log_image_discovery,
    log_image_validation,
    log_processing_stuck
)

from .log_analyzer import (
    ImageProcessingLogAnalyzer,
    analyze_recent_logs,
    find_stuck_images
)

__all__ = [
    # Core logging
    'ImageProcessorLogger',
    'ProcessingPhase',
    'LogLevel',
    'ImageContext',
    'ProcessingEvent',
    'image_logger',
    'get_image_context',
    'log_image_discovery',
    'log_image_validation',
    'log_processing_stuck',
    # Analysis tools
    'ImageProcessingLogAnalyzer',
    'analyze_recent_logs',
    'find_stuck_images'
]
