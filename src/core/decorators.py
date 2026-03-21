import asyncio
from collections.abc import Callable
from typing import Any

from loguru import logger

# Global registries for lifecycle hooks
_START_HOOKS: list[Callable[..., Any]] = []
_STOP_HOOKS: list[Callable[..., Any]] = []


def on_start(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to mark a function to be called on system start.

    Supports both sync and async functions. Registered functions will be
    executed during the `System.start()` phase.

    Args:
        func: The function to register.

    Returns:
        The original function.
    """
    _START_HOOKS.append(func)
    logger.debug(f"Registered @on_start hook: {func.__module__}.{func.__name__}")
    return func


def on_stop(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to mark a function to be called on system stop.

    Supports both sync and async functions. Registered functions will be
    executed during the `System.stop()` phase.

    Args:
        func: The function to register.

    Returns:
        The original function.
    """
    _STOP_HOOKS.append(func)
    logger.debug(f"Registered @on_stop hook: {func.__module__}.{func.__name__}")
    return func


async def _run_hooks(hooks: list[Callable[..., Any]]) -> None:
    """Helper to run a list of hooks (sync or async) sequentially.

    Args:
        hooks: A list of functions to execute.

    Raises:
        Exception: If any hook fails during execution.
    """
    for hook in hooks:
        try:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()
        except Exception as e:
            logger.error(f"Error executing lifecycle hook {hook.__name__}: {e}")
            raise


def get_start_hooks() -> list[Callable[..., Any]]:
    """Gets all registered start hooks.

    Returns:
        A list of registered start hook functions.
    """
    return _START_HOOKS


def get_stop_hooks() -> list[Callable[..., Any]]:
    """Gets all registered stop hooks.

    Returns:
        A list of registered stop hook functions.
    """
    return _STOP_HOOKS


def clear_hooks() -> None:
    """Clears all registered hooks.

    Mainly used for resetting global state during unit testing.
    """
    _START_HOOKS.clear()
    _STOP_HOOKS.clear()
    logger.debug("Cleared all lifecycle hooks")
