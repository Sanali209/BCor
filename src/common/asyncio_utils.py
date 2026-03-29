import asyncio
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
from concurrent.futures import ProcessPoolExecutor

T = TypeVar("T")

class TaskThrottler:
    """Utility to limit concurrent execution of asynchronous tasks.
    
    This is especially useful for scrapers, API clients, or any process
    that needs to stay within rate limits or resource constraints.
    """
    
    def __init__(self, concurrency_limit: int = 5):
        """Initialize the throttler.
        
        Args:
            concurrency_limit: Maximum number of concurrent tasks allowed.
        """
        self._semaphore = asyncio.Semaphore(concurrency_limit)
        self._limit = concurrency_limit

    async def run(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a function while respecting the concurrency limit.
        
        Args:
            func: The async function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.
            
        Returns:
            The result of the function execution.
        """
        async with self._semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                # Fallback for sync functions run in a thread
                return await asyncio.get_running_loop().run_in_executor(
                    None, lambda: func(*args, **kwargs)
                )

    def throttle(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to automatically throttle an async function.
        
        Args:
            func: The async function to decorate.
            
        Returns:
            A wrapped function that respects the concurrency limit.
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self._semaphore:
                return await func(*args, **kwargs)
        return wrapper

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()

    @property
    def limit(self) -> int:
        """Get the current concurrency limit."""
        return self._limit

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

    async def run(self, func: Callable[..., T], *args: Any) -> T:
        """Run a function in a separate process and await results.
        
        Args:
            func: The function to execute.
            *args: Arguments for the function.
            
        Returns:
            The result of the function execution.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    def shutdown(self):
        """Shutdown the pool and wait for workers to finish."""
        self._executor.shutdown(wait=True)

async def async_delay(seconds: float):
    """Async-friendly replacement for asyncio.sleep with explicit naming.
    
    Args:
        seconds: Number of seconds to yield execution.
    """
    await asyncio.sleep(seconds)
