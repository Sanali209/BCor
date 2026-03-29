"""
Progress Service Component for unified progress reporting to UI.

Provides a centralized system for tracking and reporting internal progress
to the user interface across all application operations.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field

from loguru import logger

from SLM.core.component import Component


@dataclass
class OperationProgress:
    """Represents the progress of a single operation."""

    operation_id: str
    operation_name: str
    current: int = 0
    total: int = 100
    status: str = "running"
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        return (self.current / self.total * 100) if self.total > 0 else 0.0

    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation_id": self.operation_id,
            "operation_name": self.operation_name,
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "status": self.status,
            "duration": self.duration,
            "metadata": self.metadata
        }


class ProgressService(Component):
    """
    Unified system for reporting internal progress to UI.

    Features:
    - Track multiple simultaneous operations
    - Real-time progress updates via message bus
    - Progress listener subscription system
    - Operation lifecycle management
    - Integration with SLM component system
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "progress_service")
        self.operations: Dict[str, OperationProgress] = {}
        self.listeners: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    async def on_initialize_async(self):
        """Initialize the progress service."""
        logger.info("Progress service initialized")
        # Set up message bus subscriptions for progress events
        await self.setup_progress_subscriptions()

    async def on_start_async(self):
        """Start the progress service."""
        logger.info("Progress service started")

    async def on_shutdown_async(self):
        """Shutdown the progress service."""
        async with self._lock:
            self.operations.clear()
            self.listeners.clear()
        logger.info("Progress service shutdown")

    async def setup_progress_subscriptions(self):
        """Set up subscriptions for progress-related events."""
        if self.message_bus:
            # Subscribe to operation start events
            self.message_bus.subscribe("progress.operation.start", self._handle_operation_start)
            self.message_bus.subscribe("progress.operation.update", self._handle_operation_update)
            self.message_bus.subscribe("progress.operation.complete", self._handle_operation_complete)
            logger.debug("Progress service message bus subscriptions set up")

    async def start_operation(
        self,
        operation_name: str,
        total_steps: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new operation.

        Args:
            operation_name: Human-readable operation name
            total_steps: Total number of steps for this operation
            metadata: Additional operation metadata

        Returns:
            Operation ID for tracking this operation
        """
        operation_id = str(uuid.uuid4())[:8]

        async with self._lock:
            operation = OperationProgress(
                operation_id=operation_id,
                operation_name=operation_name,
                total=total_steps,
                metadata=metadata or {}
            )
            self.operations[operation_id] = operation

        # Notify listeners
        await self._notify_listeners(operation_id)

        # Publish to message bus
        if self.message_bus:
            await self.message_bus.publish_async(
                "progress.operation.started",
                operation_id=operation_id,
                operation_name=operation_name,
                total_steps=total_steps,
                metadata=metadata
            )

        logger.debug(f"Started operation: {operation_name} ({operation_id})")
        return operation_id

    async def update_progress(
        self,
        operation_id: str,
        current: int,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update progress for an operation.

        Args:
            operation_id: Operation ID from start_operation
            current: Current progress value
            status: Optional status update
            metadata: Optional metadata update
        """
        async with self._lock:
            if operation_id not in self.operations:
                logger.warning(f"Unknown operation ID: {operation_id}")
                return

            operation = self.operations[operation_id]
            operation.current = current

            if status:
                operation.status = status

            if metadata:
                operation.metadata.update(metadata)

        # Notify listeners
        await self._notify_listeners(operation_id)

        # Publish to message bus
        if self.message_bus:
            await self.message_bus.publish_async(
                "progress.operation.updated",
                operation_id=operation_id,
                current=current,
                percentage=operation.percentage,
                status=status,
                metadata=metadata
            )

    async def complete_operation(
        self,
        operation_id: str,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Mark an operation as complete.

        Args:
            operation_id: Operation ID from start_operation
            status: Final status ("completed", "failed", "cancelled")
            metadata: Final metadata
        """
        async with self._lock:
            if operation_id not in self.operations:
                logger.warning(f"Unknown operation ID: {operation_id}")
                return

            operation = self.operations[operation_id]
            operation.current = operation.total
            operation.status = status

            if metadata:
                operation.metadata.update(metadata)

        # Notify listeners
        await self._notify_listeners(operation_id)

        # Publish to message bus
        if self.message_bus:
            await self.message_bus.publish_async(
                "progress.operation.completed",
                operation_id=operation_id,
                operation_name=operation.operation_name,
                status=status,
                duration=operation.duration,
                metadata=metadata
            )

        logger.info(
            f"Completed operation: {operation.operation_name} ({operation_id}) "
            f"in {operation.duration:.2f}s"
        )

    async def fail_operation(
        self,
        operation_id: str,
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Mark an operation as failed.

        Args:
            operation_id: Operation ID from start_operation
            error: The exception that caused the failure
            metadata: Additional error metadata
        """
        error_metadata = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(metadata or {})
        }

        await self.complete_operation(operation_id, "failed", error_metadata)

    def subscribe_to_operation(
        self,
        operation_id: str,
        callback: Callable[[OperationProgress], None]
    ):
        """
        Subscribe to updates for a specific operation.

        Args:
            operation_id: Operation ID to subscribe to
            callback: Function to call on progress updates
        """
        if operation_id not in self.listeners:
            self.listeners[operation_id] = []
        self.listeners[operation_id].append(callback)

    def subscribe_to_pattern(
        self,
        pattern: str,
        callback: Callable[[OperationProgress], None]
    ):
        """
        Subscribe to operations matching a pattern.

        Args:
            pattern: Pattern to match operation names against
            callback: Function to call on progress updates
        """
        if pattern not in self.listeners:
            self.listeners[pattern] = []
        self.listeners[pattern].append(callback)

    def unsubscribe(
        self,
        subscription_id: str,
        callback: Optional[Callable] = None
    ):
        """
        Unsubscribe from progress updates.

        Args:
            subscription_id: Operation ID or pattern to unsubscribe from
            callback: Specific callback to remove (removes all if None)
        """
        if subscription_id in self.listeners:
            if callback is None:
                self.listeners[subscription_id].clear()
            else:
                if callback in self.listeners[subscription_id]:
                    self.listeners[subscription_id].remove(callback)

    def get_operation(self, operation_id: str) -> Optional[OperationProgress]:
        """
        Get current progress for an operation.

        Args:
            operation_id: Operation ID

        Returns:
            OperationProgress instance or None if not found
        """
        return self.operations.get(operation_id)

    def get_all_operations(self) -> Dict[str, OperationProgress]:
        """
        Get all current operations.

        Returns:
            Dictionary of operation_id -> OperationProgress
        """
        return self.operations.copy()

    def get_active_operations(self) -> List[OperationProgress]:
        """
        Get all currently active (running) operations.

        Returns:
            List of active operations
        """
        return [
            op for op in self.operations.values()
            if op.status in ["running", "starting"]
        ]

    async def _notify_listeners(self, operation_id: str):
        """Notify all listeners about operation updates."""
        if operation_id not in self.operations:
            return

        operation = self.operations[operation_id]

        # Notify specific operation listeners
        if operation_id in self.listeners:
            for callback in self.listeners[operation_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(operation)
                    else:
                        callback(operation)
                except Exception as e:
                    logger.error(f"Error in progress listener for {operation_id}: {e}")

        # Notify pattern-based listeners
        for pattern, callbacks in self.listeners.items():
            if pattern != operation_id and self._matches_pattern(operation.operation_name, pattern):
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(operation)
                        else:
                            callback(operation)
                    except Exception as e:
                        logger.error(f"Error in pattern progress listener {pattern}: {e}")

    def _matches_pattern(self, operation_name: str, pattern: str) -> bool:
        """
        Check if operation name matches a pattern.

        Args:
            operation_name: Name of the operation
            pattern: Pattern to match against (supports wildcards)

        Returns:
            True if operation matches pattern
        """
        # Simple pattern matching - can be enhanced with regex if needed
        if pattern == "*":
            return True

        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in operation_name

        if pattern.startswith("*"):
            return operation_name.endswith(pattern[1:])

        if pattern.endswith("*"):
            return operation_name.startswith(pattern[:-1])

        return operation_name == pattern

    # Message bus event handlers
    async def _handle_operation_start(self, event_type: str, **data):
        """Handle operation start events from message bus."""
        operation_name = data.get("operation_name", "Unknown")
        total_steps = data.get("total_steps", 100)
        metadata = data.get("metadata", {})

        await self.start_operation(operation_name, total_steps, metadata)

    async def _handle_operation_update(self, event_type: str, **data):
        """Handle operation update events from message bus."""
        operation_id = data.get("operation_id")
        current = data.get("current", 0)
        status = data.get("status")
        metadata = data.get("metadata")

        if operation_id:
            await self.update_progress(operation_id, current, status, metadata)

    async def _handle_operation_complete(self, event_type: str, **data):
        """Handle operation complete events from message bus."""
        operation_id = data.get("operation_id")
        status = data.get("status", "completed")
        metadata = data.get("metadata")

        if operation_id:
            await self.complete_operation(operation_id, status, metadata)
