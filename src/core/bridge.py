from collections.abc import Callable
from typing import Any

from loguru import logger

# Lazy import legacy AppAction to avoid circular dependencies if any
try:
    from SLM.actions.action_module import AppAction
except ImportError:
    # During testing we might need to handle this
    class AppAction:  # type: ignore[no-redef]
        pass

class LegacyAllocatorBridge:
    def __init__(self, container: Any | None = None) -> None:  # noqa: ANN401
        self.container = container
        # Note: We assume SLM is already in sys.path or will be added by the caller

    def get(self, type_key: Any) -> Any:  # noqa: ANN401
        """Resolves a dependency from Dishka first, then legacy Allocator."""
        # 1. Try Dishka
        if self.container:
            try:
                return self.container.get(type_key)
            except Exception:
                pass
        
        # 2. Try Legacy Allocator
        try:
            from SLM.appGlue.core import Allocator
            return Allocator.get_instance(type_key)
        except Exception as e:
            logger.error(f"Bridge failed to resolve {type_key}: {e}")
            raise e

class BridgeAppAction(AppAction):  # type: ignore[misc]
    """A legacy AppAction that bridges to BCor MessageBus."""
    def __init__(
        self,
        name: str,
        command_cls: type,
        mapping: Callable[..., Any],
        message_bus: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:  # noqa: ANN401
        super().__init__(name=name, **kwargs)
        self.command_cls = command_cls
        self.mapping = mapping
        self.message_bus = message_bus

    def run(self, *args: Any, **kwargs: Any) -> bool:  # noqa: ANN401
        """Dispatches the command to the BCor MessageBus."""
        import asyncio
        payload = self.mapping(*args, **kwargs)
        command = self.command_cls(**payload)
        
        # Dispatch asynchronously. In a real GUI app, we might need 
        # to use loop.call_soon_threadsafe or similar.
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.message_bus.dispatch(command))
        except RuntimeError:
            # Fallback for sync contexts without loop
            asyncio.run(self.message_bus.dispatch(command))
        return True

class LegacyActionBridge:
    def __init__(self, message_bus: Any) -> None:  # noqa: ANN401
        self.message_bus = message_bus

    def register_action(self, name: str, command_cls: type, mapping: Callable[..., Any] | None = None) -> Any:  # noqa: ANN401
        """Registers a bridge action in the legacy ActionManager."""
        from SLM.actions import action_manager
        
        def default_mapping(*a: Any, **k: Any) -> dict[Any, Any]:  # noqa: ANN401
            return {}

        if mapping is None:
            mapping = default_mapping
            
        action = BridgeAppAction(
            name=name,
            command_cls=command_cls,
            mapping=mapping,
            message_bus=self.message_bus
        )
        action_manager.actions.append(action)
        return action
