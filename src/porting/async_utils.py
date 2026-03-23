import asyncio
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
from loguru import logger

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
            return await func(*args, **kwargs)

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

    @property
    def limit(self) -> int:
        """Get the current concurrency limit."""
        return self._limit
