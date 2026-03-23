import asyncio
import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import wraps
from typing import Any, Callable, TypeVar

from loguru import logger

T = TypeVar("T")

class WindowsLoopManager:
    """Manages asyncio loop policies and drainage for Windows stability.
    
    This manager provides utilities to ensure that the asyncio event loop
    behaves correctly on Windows, particularly when integrated with GUI
    frameworks like PySide6 via qasync.
    """
    
    @staticmethod
    def setup_loop():
        """Set up the appropriate event loop policy for Windows.
        
        On Windows, this applies the `WindowsSelectorEventLoopPolicy` which is
        often more stable when working with certain network and GUI operations
        compared to the default ProactorEventLoop in newer Python versions.
        """
        if platform.system() == "Windows":
            # Using SelectorEventLoop for better stability with some GUI tools
            # though Proactor is default in 3.8+.
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.debug("Applied WindowsSelectorEventLoopPolicy")

    @staticmethod
    async def drain_loop(delay: float = 0.1):
        """Allow pending tasks to settle before shutdown.
        
        Args:
            delay: Time in seconds to wait for tasks to settle.
        """
        logger.debug(f"Draining event loop for {delay}s...")
        await asyncio.sleep(delay)

class PathNormalizer:
    """Utilities for standardized path handling across different OS versions.
    
    Provides tools to normalize path casing and formatting, and a decorator
    to automatically apply these normalizations to function arguments.
    """
    
    @staticmethod
    def norm(path: str) -> str:
        """Normalize path casing and absolute formatting.
        
        Args:
            path: The path string to normalize.
            
        Returns:
            The normalized absolute path with standardized casing.
        """
        if not path:
            return path
        return os.path.normcase(os.path.abspath(path))

    @classmethod
    def normalize_args(cls, *arg_names: str):
        """Decorator to automatically normalize specific arguments as paths.
        
        Args:
            *arg_names: Names of the arguments to be normalized.
            
        Returns:
            A decorator function.
            
        Example:
            @PathNormalizer.normalize_args('file_path', 'root_dirs')
            def process_files(file_path, root_dirs):
                # file_path is now normalized str
                # root_dirs is now a list of normalized str
                ...
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs):
                import inspect
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                for name in arg_names:
                    if name in bound_args.arguments:
                        val = bound_args.arguments[name]
                        if isinstance(val, str):
                            bound_args.arguments[name] = cls.norm(val)
                        elif isinstance(val, list):
                            bound_args.arguments[name] = [cls.norm(v) if isinstance(v, str) else v for v in val]
                
                return func(*bound_args.args, **bound_args.kwargs)
            return wrapper
        return decorator

class AsyncPoolExecutor:
    """Wrapper for ProcessPoolExecutor to safely use multiprocessing with asyncio.
    
    Ensures that long-running or CPU-bound tasks can be offloaded to a
    separate process while still being awaitable from the main event loop.
    """
    
    def __init__(self, max_workers: int | None = None):
        """Initialize the executor.
        
        Args:
            max_workers: Maximum number of worker processes. Defaults to None.
        """
        self._executor = ProcessPoolExecutor(max_workers=max_workers)
        self._loop = asyncio.get_running_loop()

    async def run(self, func: Callable[..., T], *args: Any) -> T:
        """Run a function in a separate process and await results.
        
        Args:
            func: The function to execute.
            *args: Arguments for the function.
            
        Returns:
            The result of the function execution.
        """
        return await self._loop.run_in_executor(self._executor, func, *args)

    def shutdown(self):
        """Shutdown the pool and wait for workers to finish."""
        self._executor.shutdown(wait=True)

async def async_delay(seconds: float):
    """Async-friendly replacement for time.sleep.
    
    Args:
        seconds: Number of seconds to yield execution.
    """
    await asyncio.sleep(seconds)
